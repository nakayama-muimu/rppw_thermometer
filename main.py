import machine
from sys import exit
import utime
import ujson
import ssl
from umqtt.simple import MQTTClient
import utility as util
from secrets import WIFI, IOT_CORE
import thermometer

DEBUG = True
INTERVAL = 300 # sec

# Define light (Onboard Green LED) and set its default state to off
light = machine.Pin("LED", machine.Pin.OUT)
light.off()

# WiFi connection
ret, info = util.connect_wifi(ssid=WIFI['SSID'], key=WIFI['KEY'])
if not ret:
    print('Failed to connect WiFi.')
    exit()
if DEBUG:
    print('WiFi connected.')

# NTP sync
t = util.ntp_sync()
# Sync again when the day changes
day = t[2]
if DEBUG:
    print(f"ntp_sync done. {t}")

# Prepare AWS IoT Cpre topic string
CLIENT_ID = IOT_CORE['CLIENT_ID']
AWS_ENDPOINT = IOT_CORE['ENDPOINT']
PUB_TOPIC = f"{CLIENT_ID}/temperature/all"
SUB_TOPIC = f"{CLIENT_ID}/light"

# Procedure for umqtt.simple version 1.4.0

#CERT_FILE = 'certs/picoW_01.cert.pem' # PEM is not available
#KEY_FILE = 'certs/picoW_01.private.key'
#CA_FILE = 'certs/root-CA.crt'
CERT_FILE = 'certs/picoW_01.cert.der'
#KEY_FILE = 'certs/picoW_01.private.der' # NG: openssl rsa ...
KEY_FILE = 'certs/picoW_01b.private.der' # OK: openssl pkey ...
CA_FILE = 'certs/root-CA.der'

# SSL Context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_REQUIRED
context.load_verify_locations(cafile=CA_FILE)
context.load_cert_chain(CERT_FILE, KEY_FILE)
if DEBUG:
    print('SSL Context prepared.')

# MQTT client
mqtt = MQTTClient(
    client_id=CLIENT_ID,
    server=AWS_ENDPOINT,
    port=8883,
    keepalive=5000,
    ssl = context
)
if DEBUG:
    print('MQTT client prepared.')

# Establish connection to AWS IoT Core
mqtt.connect()
if DEBUG:
    print('MQTT connected.')

# Callback function for all subscriptions
def mqtt_subscribe_callback(topic, msg):
    print(f"Received topic: {topic}")
    print(ujson.loads(msg))

# Set callback for subscriptions
mqtt.set_callback(mqtt_subscribe_callback)
if DEBUG:
    print('MQTT subscription callback set.')

# Subscribe to topic
mqtt.subscribe(SUB_TOPIC)
if DEBUG:
    print('MQTT subscription started.')

# Main loop as Timer callback
# To check temperature every 5 minutes
def access_iot(timer):
    # Publish the temperature
    tmpr = thermometer.read_temperature()
    time_str = util.get_iso_datetime_string()
    print(f"{time_str} internal: {tmpr['internal']['average']}, external: {tmpr['external']['average']}")
    message = ujson.dumps({'datetime': time_str, 'temperature': tmpr})
    print(f"Publishing topic '{PUB_TOPIC}' to AWS IoT Core.")
    mqtt.publish(topic=PUB_TOPIC, msg=message, qos=0)

    # Check subscriptions for message
    mqtt.check_msg()
    
    # NTP sync after the change of date
    ut = utime.localtime()
    global day
    if ut[2] != day:
        util.ntp_sync()
        ut = utime.localtime()
        day = ut[2]
        print(f"NTP sync done. {util.get_iso_datetime_string()}")

# First publish before the invoke by timer
access_iot(None)

# Set timer
timer = machine.Timer(-1)
timer.init(mode=machine.Timer.PERIODIC, period=INTERVAL * 1000, callback=access_iot)

