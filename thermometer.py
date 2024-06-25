import machine
import utime

sensor_internal = machine.ADC(4)
sensor_external = machine.ADC(0)

conversion_factor = 3.3 / (65535)

def get_internal_temperature():
    reading = sensor_internal.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature    

def get_external_temperature():
    reading = sensor_external.read_u16() * conversion_factor
    # MCP9700A
    # 10mV per a degree C
    # 'V 0 degrees C' is 500mA
    temperature = reading * 100 - 50
    return temperature

def read_temperature(interval=1, count=10):
    int_temp_sum = get_internal_temperature()
    int_temp_max = int_temp_sum
    int_temp_min = int_temp_sum
    ext_temp_sum = get_external_temperature()
    ext_temp_max = ext_temp_sum
    ext_temp_min = ext_temp_sum
    for i in range(count - 1):
        utime.sleep(interval)
        int_temp = get_internal_temperature()
        ext_temp = get_external_temperature()
        int_temp_sum += int_temp
        int_temp_max = max(int_temp_max, int_temp)
        int_temp_min = min(int_temp_min, int_temp)
        ext_temp_sum += ext_temp
        ext_temp_max = max(ext_temp_max, ext_temp)
        ext_temp_min = min(ext_temp_min, ext_temp)
    return {
        "internal":{
            "average":int_temp_sum / count
            , "max":int_temp_max
            , "min":int_temp_min
            }
        , "external":{
            "average":ext_temp_sum / count
            , "max":ext_temp_max
            , "min":ext_temp_min
            }
        }

def wrapper(timer):
    data = read_temperature()
    print(data)
    print(data['external']['average'] - data['internal']['average'])
    #print(get_internal_temperature())
    #print(get_external_temperature())
    

if __name__ == "__main__":
    print(get_internal_temperature())
    print(get_external_temperature())
    
    '''
    while True:
        data = read_temperature()
        print(data)
        print(data['external']['average'] - data['internal']['average'])
        utime.sleep(300)
    '''
    from machine import Timer
    timer = Timer()
    timer.init(period=15000, mode=Timer.PERIODIC, callback=wrapper)


