import time
import board
import struct
import busio
import gpiod
import serial
import adafruit_dht
import adafruit_ads1x15.ads1115 as ads
from adafruit_ads1x15.analog_in import AnalogIn
import os
import numpy as np


class GH_Sensors:
    def __init__(self, general_i2c):
        self.__general_i2c = general_i2c        
        self.__Vref = 5.0 # ads source voltage
        self.__ads_resolution = 65535.0 # maximum resolution for ads sensor (16-bit)
        self.__light_sensor_resistance = 10000.0 # about 10K ohm 
        # ads channels
        self.__ads_channels = [ads.P0, ads.P1, ads.P2, ads.P3]
        self.__ads_sensor = ads.ADS1115(self.__general_i2c)        
        # moisture sensor calibration values
        self.__MOISTURE_SENSOR_VERY_DRY_VAL = 18000
        self.__MOISTURE_SENSOR_VERY_WET_VAL = 7000
        # gpiod
        self.chip = gpiod.chip('gpiochip4')


    # Soil sensor functions
    def set_soil_sensor_pins(self, RE_DE_pin, Rx_pin, Tx_pin):
        self.__soil_RE_DE_pin = RE_DE_pin
        self.__soil_Rx_pin = Rx_pin
        self.__soil_Tx_pin = Tx_pin
        # set the pin of RE & RD
        self.__soil_RE_DE_pin = self.chip.get_line(RE_DE_pin)        
        config = gpiod.line_request()
        config.consumer = "RE-DE"
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT
        self.__soil_RE_DE_pin.request(config=config, default_val=0)
        # set the uart configurations
        # self.__uart = busio.UART(self.__soil_Tx_pin, self.__soil_Rx_pin, 4800, 8, None, 1)        
        self.__uart = serial.Serial("/dev/ttyAMA0", baudrate=4800, bytesize=8, parity='N', stopbits=1, timeout=1)

    def __send_modbus_request(self):
        modbus_req = [0x01, 0x03, 0x00, 0x00, 0x00, 0x04, 0x44, 0x09]
        # GPIO.output(self.__soil_RE_DE_pin, GPIO.HIGH)
        # self.__soil_RE_DE_pin.set_value(1)
        time.sleep(0.01)
        self.__uart.write(modbus_req)
        time.sleep(0.01)
        # GPIO.output(self.__soil_RE_DE_pin, GPIO.LOW)        
        # self.__soil_RE_DE_pin.set_value(0)
    
    def __get_modbus_response(self):
        response = self.__uart.read(11) # expected 11 bytes to be received
        return response if len(response) >= 11 else None

    def get_ph(self):
        try:        
            self.__send_modbus_request()
            resp = self.__get_modbus_response()

            if resp == None:
                return 0.0

            if resp[1] != 0x03:
                print("Invalid response for Soil PH request!")
                return 0.0
            
            ph_val = struct.unpack(">H", resp[9:11])[0] / 10.0

            return ph_val
        except RuntimeError as err:
            print(f"Sensor Error: {err.args[0]}")
            return 0.0

    def get_ec(self):
        try:            
            self.__send_modbus_request()
            resp = self.__get_modbus_response()

            if resp == None:
                return 0.0

            if resp[1] != 0x03:
                print("Invalid response for Soil EC request!")
                return 0.0
            
            ec_val = struct.unpack(">H", resp[7:9])[0]

            return ec_val
        except RuntimeError as err:
            print(f"Sensor Error: {err.args[0]}")
            return 0.0

    def get_soil_humidity(self):
        try:
            self.__send_modbus_request()
            resp = self.__get_modbus_response()

            if resp == None:
                return 0.0

            if resp[1] != 0x03:
                print("Invalid response for Soil Humidity request!")
                return 0.0
            
            humi_val = struct.unpack(">H", resp[3:5])[0] / 10.0

            return humi_val
        except RuntimeError as err:
            print(f'Sensor Error: {err.args[0]}')
            return 0.0
    
    def get_soil_temperature(self):
        try:            
            self.__send_modbus_request()
            resp = self.__get_modbus_response()

            if resp == None:
                return 0.0
            
            if resp[1] != 0x03:
                print("Invalid response for Soil Temperature request!")
                return 0.0
            
            temp_val = struct.unpack(">H", resp[5:7])[0] / 10.0

            return temp_val
        except RuntimeError as err:
            print(f'Sensor Error: {err.args[0]}')
            return 0.0

    # ads soil moisture
    def set_soil_moisture_ads1115_channel(self, ch):
        self.__ads_moisture = AnalogIn(self.__ads_sensor, self.__ads_channels[ch])

    def calibrate_soil_moisture_ads1115(self, dry_value, wet_value):
        self.__MOISTURE_SENSOR_VERY_DRY_VAL = dry_value
        self.__MOISTURE_SENSOR_VERY_WET_VAL = wet_value

    def get_soil_moisture_ads1115(self):
        try:
            moisture_raw = self.__ads_moisture.value
            moisture_perc = np.interp(moisture_raw, [self.__MOISTURE_SENSOR_VERY_WET_VAL, self.__MOISTURE_SENSOR_VERY_DRY_VAL], [100, 0])
            return moisture_perc
        except RuntimeError as err:
            print(f'Sensor Error: {err.args[0]}')
            return 0.0

    # dht22 functions
    def set_dht22_pin(self, pin):
        self.__dht22 = adafruit_dht.DHT22(pin)

    def get_air_temperature_C(self):
        try:
            tempC = self.__dht22.temperature
            if tempC == None:
                return 0
            
            return tempC
        except RuntimeError as err:
            print(f"Sensors: {err.args[0]}")
            return 0
    
    def get_air_temperature_F(self):
        try:
            tempC = self.get_air_temperature_C()
            if tempC == None:
                return 0
            
            return tempC * (9.0/5.0) + 32.0
        except RuntimeError as err:
            print(f"Sensors: {err.args[0]}")
            return 0

    def get_air_humidity(self):
        try:
            hum = self.__dht22.humidity
            if hum == None:
                return 0
            
            return hum
        except RuntimeError as err:
            print(f"Sensors: {err.args[0]}")
            return 0

    # light intensity functions
    def set_light_intensity_ads1115_channel(self, ch):
        self.ads_light = AnalogIn(self.__ads_sensor, self.__ads_channels[ch])

    def __get_lux_raw(self):
        return self.ads_light.value

    def __get_lux_voltage(self, ads_reading = 0.0):
        return self.ads_light.voltage
    
    def __get_lux_current(self, voltage = 0.0):
        try:            
            return voltage / self.__light_sensor_resistance
        except RuntimeError as err:
            print(f'Sensor Error: {err.args[0]}')
            return 0.0
    
    def get_light_intensity(self):
        try:
            return self.__get_lux_current(self.__get_lux_voltage()) * 1000000.0 * 2.0
        except RuntimeError as err:
            print(f'Sensor Error: {err.args[0]}')
            return 0.0