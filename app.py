import time
import board
import busio
import os
from sensors import GH_Sensors
# dht22 setup
dht22_pin = board.D26
# soil moisture setup
RE_RD = 13
TX = 14
RX = 15
#ads1115 soil moisture setup
ads1115_soil_ch = 0
# ads1115 light setup
ads1115_light_ch = 1
# initialize the i2c
i2c = busio.I2C(board.SCL, board.SDA)

# initialize the application sensors
env_sensors = GH_Sensors(i2c)
env_sensors.set_dht22_pin(dht22_pin)
env_sensors.set_soil_moisture_ads1115_channel(ads1115_soil_ch)
env_sensors.set_light_intensity_ads1115_channel(ads1115_light_ch)
env_sensors.calibrate_soil_moisture_ads1115(18000, 7000)
env_sensors.set_soil_sensor_pins(RE_RD, RX, TX)

while True:
	os.system('clear') # clear the terminal
	print("**************************************************")
	print(f'Air Temperature (C): {env_sensors.get_air_temperature_C()} C')
	print(f'Air Temperature (F): {env_sensors.get_air_temperature_F()} F')
	print(f'Air Humidity (%): {env_sensors.get_air_humidity()} %')
	print("**************************************************")
	print(f'ADS1115 Soil Humidity (%): {env_sensors.get_soil_moisture_ads1115()} %')
	print(f'ADS1115 Light Intensity (Lux): {env_sensors.get_light_intensity()} Lux')
	print("**************************************************")
	print(f'Soil PH: {env_sensors.get_ph()}')
	print(f'Soil EC (uS/cm): {env_sensors.get_ec()} uS/cm')
	print(f'Soil Temperature (C): {env_sensors.get_soil_temperature()} C')
	print(f'Soil Humidity (%): {env_sensors.get_soil_humidity()} %')
	print("**************************************************")
	time.sleep(5)