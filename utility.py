import network
import utime
import ntptime
import machine

def connect_wifi(ssid='', key='', max_trial=20, show_info=False):

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, key)

    counter = 0
    while wlan.isconnected() == False:
        counter += 1
        if show_info:
            print(f'Trying to connecting to WiFI... count:{counter}')
        if counter == max_trial:
            if show_info:
                print('Can not connect to WiFi')
            return False, None
        utime.sleep(1)
    
    wlan_status = wlan.ifconfig()
    if show_info:
        print(f'IP address: {wlan_status[0]}')
        print(f'Netmask: {wlan_status[1]}')
        print(f'Default gateway: {wlan_status[2]}')
        print(f'Name server: {wlan_status}')

    return True, wlan_status

def ntp_sync(show_info=False):
    rtc = machine.RTC()
    if(show_info):
        print(f"Before sync:")
        print(f"utime.localtime() = {utime.localtime()}")
        print(f"rtc.datetime() = {rtc.datetime()}")
    ntptime.settime()
    JST_OFFSET = 9 * 60 * 60 # 9h (= 32400s)
    ut = utime.localtime(utime.time() + JST_OFFSET)
    rtc.datetime( (ut[0], ut[1], ut[2], ut[6]+1, ut[3], ut[4], ut[5], 0) )
    if(show_info):
        print(f"After sync:")
        print(utime.localtime())
        print(rtc.datetime())
    
    return ut

def get_iso_datetime_string(tz_offset='+09:00'):
    ut = utime.localtime()
    return f"{ut[0]}-{ut[1]:0>2d}-{ut[2]:0>2d}T{ut[3]:0>2d}:{ut[4]:0>2d}:{ut[5]:0>2d}{tz_offset}"
