import time
import board
import busio
import os
from sensors import GH_Sensors
from actuators import GH_Actuators
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

# initialize the application actuators
env_actuators = GH_Actuators(0)
env_actuators.set_heater_pins(18, 18)
env_actuators.set_light_pins(23)
env_actuators.set_water_pump_pins(24)
env_actuators.set_fan_pins(25)

# scenario 1: turn on all together
def scenario_1():
	env_actuators.turn_on_heater()
	env_actuators.turn_on_light()
	env_actuators.turn_on_water_pump()
	env_actuators.turn_on_fan()
# scenario 2: turn off all together
def scenario_2():
	env_actuators.turn_off_heater()
	env_actuators.turn_off_light()
	env_actuators.turn_off_water_pump()
	env_actuators.turn_off_fan()

# scenario 3: turn on heater and light
def scenario_3():
	env_actuators.turn_on_heater()
	env_actuators.turn_on_light()
	env_actuators.turn_off_water_pump()
	env_actuators.turn_off_fan()

# scenario 4: turn on heater and fan
def scenario_4():
	env_actuators.turn_on_heater()
	env_actuators.turn_off_light()
	env_actuators.turn_off_water_pump()
	env_actuators.turn_on_fan()

# scenario 5: turn on light and fan
def scenario_5():
	env_actuators.turn_off_heater()
	env_actuators.turn_on_light()
	env_actuators.turn_off_water_pump()
	env_actuators.turn_on_fan()

# scenario 6: turn on water pump
def scenario_6():
	env_actuators.turn_off_heater()
	env_actuators.turn_off_light()
	env_actuators.turn_on_water_pump()
	env_actuators.turn_off_fan()

# scenario 7: turn on heater
def scenario_7():
	env_actuators.turn_on_heater()
	env_actuators.turn_off_light()
	env_actuators.turn_off_water_pump()
	env_actuators.turn_off_fan()

# scenario 8: turn on light
def scenario_8():
	env_actuators.turn_off_heater()
	env_actuators.turn_on_light()
	env_actuators.turn_off_water_pump()
	env_actuators.turn_off_fan()

# scenario 9: turn on fan
def scenario_9():
	env_actuators.turn_off_heater()
	env_actuators.turn_off_light()
	env_actuators.turn_off_water_pump()
	env_actuators.turn_on_fan()

# scenario 10: turn on heater and water pump
def scenario_10():
	env_actuators.turn_on_heater()
	env_actuators.turn_off_light()
	env_actuators.turn_on_water_pump()
	env_actuators.turn_off_fan()

# scenario 11: turn on light and water pump
def scenario_11():
	env_actuators.turn_off_heater()
	env_actuators.turn_on_light()
	env_actuators.turn_on_water_pump()
	env_actuators.turn_off_fan()

# scenario 12: turn on fan and water pump
def scenario_12():
	env_actuators.turn_off_heater()
	env_actuators.turn_off_light()
	env_actuators.turn_on_water_pump()
	env_actuators.turn_on_fan()

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

	# run the scenarios
	scenario_1()
	time.sleep(10)

	scenario_2()
	time.sleep(10)

	scenario_3()
	time.sleep(10)

	scenario_4()
	time.sleep(10)

	scenario_5()
	time.sleep(10)

	scenario_6()
	time.sleep(10)

	scenario_7()
	time.sleep(10)

	scenario_8()
	time.sleep(10)

	scenario_9()
	time.sleep(10)

	scenario_10()
	time.sleep(10)

	scenario_11()
	time.sleep(10)

	scenario_12()
	time.sleep(10)