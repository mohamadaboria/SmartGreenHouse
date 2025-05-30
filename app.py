import time
import datetime
import board
import busio
import os
from Sensors.sensors import GH_Sensors
from Actuators.actuators import GH_Actuators
from mqtt_handler import MqttHandler
from mongo_db_handler import MongoDBHandler
from aws_s3_handler import S3Handler
from rpi_camera import GH_Camera
from setpoints import GH_Setpoints
from serial_logger import serial_logger_task
import threading
import numpy as np
from simple_pid import PID

# # dht22 setup
dht22_pin = board.D26

# water flow sensor setup
water_flow_sensor_pin = 12
# #ads1115 soil moisture setup
ads1115_soil_ch = 0
# # ads1115 light setup
ads1115_light_ch = 1
# # initialize the i2c
i2c = busio.I2C(board.SCL, board.SDA)

# initialize the application sensors
env_sensors = GH_Sensors(i2c)
env_sensors.set_dht22_pin(dht22_pin)
env_sensors.set_soil_moisture_ads1115_channel(ads1115_soil_ch)
env_sensors.set_light_intensity_ads1115_channel(ads1115_light_ch)
env_sensors.calibrate_soil_moisture_ads1115(18000, 7000)
env_sensors.set_soil_sensor_pins()
env_sensors.set_electricity_sensor_pin()
env_sensors.set_water_flow_sensor_pin(water_flow_sensor_pin)

# initialize the application actuators
env_actuators = GH_Actuators(0x30, i2c, 'big')
# reset the esp
env_actuators.restart_esp32()
last_date_time = datetime.datetime.now()
print("Initializing actuators...", end='')
while datetime.datetime.now() - last_date_time < datetime.timedelta(seconds=10):
    print(".", end='')
    time.sleep(1)

# pin 16, channel 0, frequency 5000 Hz, duty cycle 0
while not env_actuators.setup_light_strip_1_esp32(pin=16, channel=0, timer_src=0, frequency=5000, duty_cycle=0):
    print("sending light strip 1 setup command again...")
    time.sleep(5)

time.sleep(1)

# pin 16, channel 0, frequency 5000 Hz, duty cycle 0
while not env_actuators.setup_light_strip_2_esp32(pin=15, channel=5, timer_src=0, frequency=5000, duty_cycle=0):
    print("sending light strip 2 setup command again...")
    time.sleep(5)

time.sleep(1)

# pin 17, channel 1, frequency 10 Hz, duty cycle 0
while not env_actuators.setup_heater_esp32(pin=17, channel=1, timer_src=1, frequency=50, duty_cycle=0):
    print("sending heater setup command again...")
    time.sleep(5)

time.sleep(1)
# pin 18, channel 2, frequency 25000 Hz, duty cycle 0
while not env_actuators.setup_heater_fan_esp32(pin=18, channel=2, timer_src=0, frequency=5000, duty_cycle=0):
    print("sending heater fan setup command again...")
    time.sleep(5)

time.sleep(1)
# pin 19, channel 3, frequency 25000 Hz, duty cycle 0
while not env_actuators.setup_fan_esp32(pin=19, channel=3, timer_src=0, frequency=5000, duty_cycle=0):
    print("sending fan setup command again...")
    time.sleep(5)

time.sleep(5)
# pin 23, channel 4, frequency 1000 Hz, duty cycle 0
while not env_actuators.setup_water_pump_esp32(pin=33, channel=4, timer_src=2, frequency=1000, duty_cycle=0):
    print("sending water pump setup command again...")
    time.sleep(5)

time.sleep(1)

# initialize the mqtt handler
mqtt_handler = MqttHandler("33ea71e0e0034036b86bee133525b810.s1.eu.hivemq.cloud", 8883, "SmartGreenHouse", "SmartGreenHouse2025")

# initialize the mongo db handler
mongo_db_handler = MongoDBHandler(
    "mongodb+srv://smartGh-00:Smartgreenhouse1@greenhouse.ibf6l7y.mongodb.net/?retryWrites=true&w=majority&appName=GreenHouse", "GreenHouse")

# initialize the setpoints
setpoints = GH_Setpoints(mqtt_handler, mongo_db_handler)

def set_all_light_strip_dc(duty_cycle = 0):
    """Set the duty cycle for both light strips"""
    while not env_actuators.set_light_strip_1_duty_cycle(duty_cycle):
        print("Setting light strip 1 duty cycle again...")
        time.sleep(0.1)

    while not env_actuators.set_light_strip_2_duty_cycle(duty_cycle):
        print("Setting light strip 2 duty cycle again...")
        time.sleep(0.1)

# set the subscriptions and publications
mqtt_handler.set_subscription("env_monitoring_system/actuators/heater_fan/dc", env_actuators.set_heater_fan_duty_cycle)
mqtt_handler.set_subscription("env_monitoring_system/actuators/heater/dc", env_actuators.set_heater_duty_cycle)
mqtt_handler.set_subscription("env_monitoring_system/actuators/light/dc", set_all_light_strip_dc)
mqtt_handler.set_subscription("env_monitoring_system/actuators/water_pump/dc", env_actuators.set_water_pump_duty_cycle)
mqtt_handler.set_subscription("env_monitoring_system/actuators/fan/dc", env_actuators.set_fan_duty_cycle)
mqtt_handler.set_subscription("loops/setpoints/temperature", setpoints.set_temperature_setpoint)
mqtt_handler.set_subscription("loops/setpoints/light_intensity", setpoints.set_light_setpoint)
mqtt_handler.set_subscription("loops/setpoints/soil_moisture", setpoints.set_soil_humidity_setpoint)
mqtt_handler.set_subscription("loops/setpoints/water_flow", setpoints.set_water_flow_setpoint)
mqtt_handler.set_subscription("loops/setpoints/operation_mode", setpoints.set_operation_mode)

# set the publications
mqtt_handler.set_publish("env_monitoring_system/sensors/air_temperature_C", 0, True)
mqtt_handler.set_publish("env_monitoring_system/sensors/air_humidity", 0, True)
mqtt_handler.set_publish("env_monitoring_system/sensors/light_intensity", 0, True)
mqtt_handler.set_publish("env_monitoring_system/sensors/soil_ph", 0, True)
mqtt_handler.set_publish("env_monitoring_system/sensors/soil_ec", 0, True)
mqtt_handler.set_publish("env_monitoring_system/sensors/soil_temp", 0, True)
mqtt_handler.set_publish("env_monitoring_system/sensors/soil_humidity", 0, True)
mqtt_handler.set_publish("env_monitoring_system/sensors/water_flow", 0, True)
mqtt_handler.set_publish("env_monitoring_system/actuators/heater_fan/state", 0, True)
mqtt_handler.set_publish("env_monitoring_system/actuators/heater/state", 0, True)
mqtt_handler.set_publish("env_monitoring_system/actuators/light/state", 0, True)
mqtt_handler.set_publish("env_monitoring_system/actuators/water_pump/state", 0, True)
mqtt_handler.set_publish("env_monitoring_system/actuators/fan/state", 0, True)

# create the collections in the database
mongo_db_handler.create_collection("sensors_data", "air temp", mongo_db_handler.sensor_field_doc_temp(
    "dht22.temperature", "temperature", 0.0, "C"))
mongo_db_handler.create_collection("sensors_data", "air humidity", mongo_db_handler.sensor_field_doc_temp(
    "dht22.humidity", "humidity", 0.0, "%"))
mongo_db_handler.create_collection("sensors_data", "light intensity", mongo_db_handler.sensor_field_doc_temp(
    "ads1115.light_intensity", "intensity", 0.0, "Lux"))
mongo_db_handler.create_collection(
    "sensors_data", "soil ph", mongo_db_handler.sensor_field_doc_temp("soil_ph", "ph", 0.0, "pH"))
mongo_db_handler.create_collection(
    "sensors_data", "soil ec", mongo_db_handler.sensor_field_doc_temp("soil_ec", "ec", 0.0, "uS/cm"))
mongo_db_handler.create_collection("sensors_data", "soil temp", mongo_db_handler.sensor_field_doc_temp(
    "soil_temp", "temperature", 0.0, "C"))
mongo_db_handler.create_collection("sensors_data", "soil humidity", mongo_db_handler.sensor_field_doc_temp(
    "soil_humidity", "humidity", 0.0, "%"))
mongo_db_handler.create_collection("sensors_data", "water flow", mongo_db_handler.sensor_field_doc_temp(
    "water_flow", "flow", 0.0, "L/min"))

# create the actuators collections in the database
mongo_db_handler.create_collection(
    "actuators_data", "heater", mongo_db_handler.actuator_field_doc_temp("heater", "heater", 0))
mongo_db_handler.create_collection(
    "actuators_data", "light", mongo_db_handler.actuator_field_doc_temp("light", "light", 0))
mongo_db_handler.create_collection(
    "actuators_data", "water pump", mongo_db_handler.actuator_field_doc_temp("water_pump", "water pump", 0))
mongo_db_handler.create_collection(
    "actuators_data", "fan", mongo_db_handler.actuator_field_doc_temp("fan", "fan", 0))

# create the setpoints collections in the database
mongo_db_handler.create_collection("plant_images", "plant image", {
                                   "_id": "", "image": "", "timestamp": 0})

s3_handler = S3Handler("smartgreenhouse-2025", "eu-north-1")
IMAGE_CAP_INTERVAL = 6  # hours interval to capture the image (every x hours)

# init the camera
camera = GH_Camera()

temperature_semaphore = threading.Semaphore(1)
temperature_pause_event = threading.Event()
temperature_pause_event.set()

light_semaphore = threading.Semaphore(1)
light_pause_event = threading.Event()
light_pause_event.set()

soil_semaphore = threading.Semaphore(1)
soil_pause_event = threading.Event()
soil_pause_event.set()

electricity_semaphore = threading.Semaphore(1)
electricity_pause_event = threading.Event()
electricity_pause_event.set()

water_flow_semaphore = threading.Semaphore(1)

def temperature_sp_adjustment_task():
    # PID controller parameters - easily tunable
    KP_TEMP = 1034.05  # Proportional gain
    KI_TEMP = 1.52  # Integral gain
    KD_TEMP = 0.0  # Derivative gain
    
    # Output limits for bidirectional control (-1 to 1)
    # Negative values for cooling, positive for heating
    OUTPUT_LIMITS = (-1, 1)
    
    # Sample time in seconds
    SAMPLE_TIME = 10
    
    # Deadband to prevent rapid switching between heating and cooling
    DEADBAND = 0.2  # °C
    
    # Actuator power limits
    MIN_POWER = 500
    MAX_POWER = 4095
    POWER_RANGE = MAX_POWER - MIN_POWER
    
    # Create a single PID controller for both heating and cooling
    # Error = setpoint - measurement
    # Positive error (temp < setpoint) produces positive output (heating)
    # Negative error (temp > setpoint) produces negative output (cooling)
    temperature_pid = PID(KP_TEMP, KI_TEMP, KD_TEMP, 
                         setpoint=0, 
                         sample_time=SAMPLE_TIME, 
                         output_limits=OUTPUT_LIMITS)
    temperature_pid.proportional_on_measurement = False  # Use error directly
    
    while True:
        temperature_pause_event.wait()  # Wait until the event is set
        
        # Read temperature setpoint safely
        temperature_set_point = setpoints.get_temperature_setpoint()
        
        # Update setpoint for the controller
        temperature_pid.setpoint = temperature_set_point
        
        # Read temperature safely
        try:
            temperature_semaphore.acquire()
            current_temp = env_sensors.get_air_temperature_C()
        except Exception as e:
            print(f"Error reading temperature: {e}")
            continue
        finally:
            temperature_semaphore.release()
        
        # Calculate control output using PID
        # Positive output = heating needed
        # Negative output = cooling needed
        # Output near zero = within deadband
        raw_output = temperature_pid(current_temp)
        
                # Anti-windup logic: If output is saturated, prevent integral accumulation
        if (raw_output >= OUTPUT_LIMITS[1] and (temperature_set_point - current_temp) > 0) or \
           (raw_output <= OUTPUT_LIMITS[0] and (temperature_set_point - current_temp) < 0):
            # Skip integral accumulation when output is clamped
            temperature_pid._integral -= (temperature_set_point - current_temp) * KI_TEMP * SAMPLE_TIME
        
        control_output = raw_output

        # Apply deadband to prevent oscillation
        if abs(temperature_set_point - current_temp) < DEADBAND:
            # Within deadband - no action needed
            control_output = 0
        
        # Apply control based on output sign
        if control_output > 0:  # Positive output = heating
            # Scale heating power from 0-1 range to MIN_POWER-MAX_POWER range
            heat_power_scaled = control_output # This is 0 to 1
            heater_duty_cycle = int(MIN_POWER + (POWER_RANGE * heat_power_scaled))
            heater_duty_cycle = max(MIN_POWER, min(MAX_POWER, heater_duty_cycle)) # Clamp to be safe
            
            # Apply heating
            env_actuators.set_heater_duty_cycle(heater_duty_cycle)
            env_actuators.set_heater_fan_duty_cycle(heater_duty_cycle)  # Heater fan matches heater
            env_actuators.set_fan_duty_cycle(0)  # Cooling fan off
            
        elif control_output < 0:  # Negative output = cooling
            # Scale cooling power from 0-1 range (abs value) to MIN_POWER-MAX_POWER range
            cool_power_scaled = abs(control_output) # This is 0 to 1
            fan_duty_cycle = int(MIN_POWER + (POWER_RANGE * cool_power_scaled))
            fan_duty_cycle = max(MIN_POWER, min(MAX_POWER, fan_duty_cycle)) # Clamp to be safe
            
            # Turn off heating
            while not env_actuators.set_heater_duty_cycle(0):
                time.sleep(0.1)
            while not env_actuators.set_heater_fan_duty_cycle(0):
                time.sleep(0.1)
            
            # Apply cooling
            while not env_actuators.set_fan_duty_cycle(fan_duty_cycle):
                time.sleep(0.1)
            
        else:  # Output is zero (within deadband or exactly at setpoint)
            # Turn everything off
            while not env_actuators.set_heater_duty_cycle(0):
                time.sleep(0.1)
            while not env_actuators.set_heater_fan_duty_cycle(0):
                time.sleep(0.1)
            while not env_actuators.set_fan_duty_cycle(0):
                time.sleep(0.1)
        
        time.sleep(SAMPLE_TIME)


def light_sp_adjustment_task():
    # PID controller parameters - easily tunable
    KP_LIGHT = 20  # Proportional gain -> 75 
    KI_LIGHT = 7.5  # Integral gain -> 55
    KD_LIGHT = 0.1  # Derivative gain -> 22
    
    # Output limits (0-4095 for direct duty cycle)
    OUTPUT_LIMITS = (0, 4095)
    
    # Sample time in seconds
    SAMPLE_TIME = 0.1
    
    # Create PID controller for light
    light_pid = PID(KP_LIGHT, KI_LIGHT, KD_LIGHT, setpoint=0, sample_time=SAMPLE_TIME, output_limits=OUTPUT_LIMITS)
    light_pid.proportional_on_measurement = False  # Use error directly
    
    # Previous setpoint to detect changes
    prev_set_point = 0
    
    while True:
        light_pause_event.wait()  # Wait until the event is set
        
        # Read light setpoint
        light_set_point = setpoints.get_light_setpoint()
        
        # Update PID setpoint
        light_pid.setpoint = light_set_point
        
        # Read light intensity safely
        try:
            light_semaphore.acquire()
            light_intensity = env_sensors.get_light_intensity()
        except Exception as e:
            print(f"Error reading light sensor: {e}")
            continue
        finally:
            light_semaphore.release()
        
        # If setpoint changes, reset the PID controller to avoid integral windup
        if prev_set_point != light_set_point:
            light_pid.reset()
            prev_set_point = light_set_point
        
        # Only adjust if setpoint is greater than 0 (we want some light)
        if light_set_point > 0:
            # Calculate duty cycle using PID
            duty_cycle = light_pid(light_intensity)
            
            # Apply duty cycle to light
            while not env_actuators.set_light_strip_1_duty_cycle(int(duty_cycle)):
                time.sleep(0.1)
                
            while not env_actuators.set_light_strip_2_duty_cycle(int(duty_cycle)):
                time.sleep(0.1)
        else:
            # Turn off lights if setpoint is 0
            while not env_actuators.set_light_strip_1_duty_cycle(0):
                time.sleep(0.1)
                        
            while not env_actuators.set_light_strip_2_duty_cycle(0):
                time.sleep(0.1)

            # Reset PID to prevent integral windup
            light_pid.reset()
        
        time.sleep(SAMPLE_TIME)


def set_soil_moisture_setpoint_task():
    PUMP_DUTY_CYCLE = 2047  # Full power for the pump
    WATER_Q = 500  # milliliters
    SLEEP_INTERVAL = 5 * 60  # seconds (5 minutes)
    while True:
        soil_pause_event.wait()  # Wait until the event is set
        # read the soil moisture setpoint
        mo_set_point = setpoints.get_soil_humidity_setpoint()

        # read the soil moisture value
        soil_semaphore.acquire()
        try:
            _, _, soil_humidity, _ = env_sensors.get_soil_values()
        except Exception as e:
            print(f"Error reading soil moisture: {e}")
            continue
        finally:
            soil_semaphore.release()

        # check if the soil moisture is below the setpoint
        if soil_humidity < mo_set_point:
            # turn on the water pump
            while not env_actuators.set_water_pump_duty_cycle(PUMP_DUTY_CYCLE):
                time.sleep(0.1)
            print("Water pump ON")
            total_added = 0
            while total_added < WATER_Q:
                # read the water flow rate
                water_flow_semaphore.acquire()
                try:
                    water_flow = env_sensors.get_water_flow_rate()  # L/min
                    water_flow_mil_sec = (water_flow * 1000) / 60  # L/s
                except Exception as e:
                    print(f"Error reading water flow: {e}")
                    continue
                finally:
                    water_flow_semaphore.release()

                # calculate the total added water
                if water_flow_mil_sec > 0:
                    total_added += water_flow_mil_sec
                    time.sleep(1)  # wait for 1 second
                else:
                    print("Water flow is 0, pump isn't working")
                    break
            # time.sleep(2.25)  # wait for 10 seconds to let the pump run
            # turn off the water pump
            while not env_actuators.set_water_pump_duty_cycle(0):
                time.sleep(0.1)
            print("Water pump OFF")

        time.sleep(SLEEP_INTERVAL)

serial_logger_thread = None

def app_task():
    global serial_logger_thread

    last_time_captured = datetime.datetime.now() - datetime.timedelta(hours=IMAGE_CAP_INTERVAL)
    last_sensor_update = datetime.datetime.now() - datetime.timedelta(seconds=30)
    last_actuators_update = datetime.datetime.now() - datetime.timedelta(seconds=1)
    prev_light_duty_cycle = 0.0
    prev_heater_duty_cycle = 0.0
    prev_heater_fan_duty_cycle = 0.0
    prev_fan_duty_cycle = 0.0
    prev_water_pump_duty_cycle = 0.0

    # start the serial logger task
    serial_logger_thread = threading.Thread(target=serial_logger_task, args=(env_sensors, env_actuators, temperature_semaphore, light_semaphore, soil_semaphore, water_flow_semaphore, electricity_semaphore))
    serial_logger_thread.start()
    
    # set manual operation mode
    setpoints.set_operation_mode("manual")
    while True:

        if (datetime.datetime.now() - last_sensor_update).total_seconds() > 30:
            temperature_semaphore.acquire()
            try:
                air_temp_c = env_sensors.get_air_temperature_C()
                air_temp_f = env_sensors.get_air_temperature_F()
                air_humidity = env_sensors.get_air_humidity()
            finally:
                temperature_semaphore.release()

            light_semaphore.acquire()
            try:
                light_intensity = env_sensors.get_light_intensity()
            finally:
                light_semaphore.release()

            soil_semaphore.acquire()
            try:
                soil_ph, soil_ec, soil_humidity, soil_temp = env_sensors.get_soil_values()
            finally:
                soil_semaphore.release()


            try:
                voltage, current, power, energy, frequency, power_factor, alarm = env_sensors.get_electricity_values()
            except Exception as e:
                print(f"Error reading electricity sensor: {e}")                


            water_flow_semaphore.acquire()
            try:
                water_flow = env_sensors.get_water_flow_rate()
            finally:
                water_flow_semaphore.release()

            print("**************************************************")
            print(f'Air Temperature (C): {air_temp_c} C')
            print(f'Air Temperature (F): {air_temp_f} F')
            print(f'Air Humidity (%): {air_humidity} %')
            print("**************************************************")
            print(f'ADS1115 Light Intensity (Lux): {light_intensity} Lux | veml = {env_sensors.get_light_intensity_veml()} lux')
            print("**************************************************")
            print(f'Soil PH: {soil_ph}')
            print(f'Soil EC (uS/cm): {soil_ec} uS/cm')
            print(f'Soil Temperature (C): {soil_temp} C')
            print(f'Soil Humidity (%): {soil_humidity} %')
            print("**************************************************")
            print(f'Water Flow: {water_flow} L/min')            
            print("**************************************************")
            print(f'Voltage: {voltage} V')
            print(f'Current: {current} A')
            print(f'Power: {power} W')
            print(f'Energy: {energy} Wh')
            print(f'Frequency: {frequency} Hz')
            print(f'Power Factor: {power_factor}')
            print(f'Alarm: {alarm}')
            print("**************************************************")
            last_sensor_update = datetime.datetime.now()
                
            # send the data to the mqtt broker
            mqtt_handler.publish("env_monitoring_system/sensors/air_temperature_C", air_temp_c)
            mqtt_handler.publish("env_monitoring_system/sensors/air_humidity", air_humidity)
            mqtt_handler.publish("env_monitoring_system/sensors/light_intensity", light_intensity)
            mqtt_handler.publish("env_monitoring_system/sensors/soil_ph", soil_ph)
            mqtt_handler.publish("env_monitoring_system/sensors/soil_ec", soil_ec)
            mqtt_handler.publish("env_monitoring_system/sensors/soil_temp", soil_temp)
            mqtt_handler.publish("env_monitoring_system/sensors/soil_humidity", soil_humidity)
            mqtt_handler.publish("env_monitoring_system/sensors/water_flow", water_flow)

            # send to database
            mongo_db_handler.insert_sensor_data("air temp", air_temp_c)
            mongo_db_handler.insert_sensor_data("air humidity", air_humidity)
            mongo_db_handler.insert_sensor_data("light intensity", light_intensity)
            mongo_db_handler.insert_sensor_data("soil ph", soil_ph)
            mongo_db_handler.insert_sensor_data("soil ec", soil_ec)
            mongo_db_handler.insert_sensor_data("soil temp", soil_temp)
            mongo_db_handler.insert_sensor_data("soil humidity", soil_humidity)
            mongo_db_handler.insert_sensor_data("water flow", water_flow)
        
        # update the actuators data
        if (datetime.datetime.now() - last_actuators_update).total_seconds() > 1:
            last_actuators_update = datetime.datetime.now()
            # read the actuators data
            heater_fan_duty_cycle = env_actuators.get_heater_fan_duty_cycle()
            heater_duty_cycle = env_actuators.get_heater_duty_cycle()
            light_duty_cycle = env_actuators.get_light_strip_1_duty_cycle()
            water_pump_duty_cycle = env_actuators.get_water_pump_duty_cycle()
            fan_duty_cycle = env_actuators.get_fan_duty_cycle()
            
            if heater_fan_duty_cycle != prev_heater_fan_duty_cycle:
                prev_heater_fan_duty_cycle = heater_fan_duty_cycle
                # send the data to the mqtt broker
                if heater_fan_duty_cycle == 0:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/heater_fan/state", 'Off')
                else:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/heater_fan/state", f'On at {heater_fan_duty_cycle * 100 / 4095:.2f}%')
                    
                # send to database
                mongo_db_handler.insert_actuator_data(
                    "heater fan", heater_fan_duty_cycle)

            if heater_duty_cycle != prev_heater_duty_cycle:
                prev_heater_duty_cycle = heater_duty_cycle
                # send the data to the mqtt broker
                if heater_duty_cycle == 0:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/heater/state", 'Off')
                else:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/heater/state", f'On at {heater_duty_cycle * 100 / 4095:.2f}%')
                    
                # send to database
                mongo_db_handler.insert_actuator_data(
                    "heater", heater_duty_cycle)
            
            if light_duty_cycle != prev_light_duty_cycle:
                prev_light_duty_cycle = light_duty_cycle
                # send the data to the mqtt broker
                if light_duty_cycle == 0:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/light/state", 'Off')
                else:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/light/state", f'On at {light_duty_cycle * 100 / 4095:.2f}%')
                    
                # send to database
                mongo_db_handler.insert_actuator_data(
                    "light", light_duty_cycle)
                    
            if water_pump_duty_cycle != prev_water_pump_duty_cycle:
                prev_water_pump_duty_cycle = water_pump_duty_cycle
                # send the data to the mqtt broker
                if water_pump_duty_cycle == 0:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/water_pump/state", 'Off')
                else:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/water_pump/state", f'On at {water_pump_duty_cycle * 100 / 4095:.2f}%')
                    
                # send to database
                mongo_db_handler.insert_actuator_data(
                    "water pump", water_pump_duty_cycle)
                    
            if fan_duty_cycle != prev_fan_duty_cycle:
                prev_fan_duty_cycle = fan_duty_cycle
                # send the data to the mqtt broker
                if fan_duty_cycle == 0:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/fan/state", 'Off')
                else:
                    mqtt_handler.publish(
                        "env_monitoring_system/actuators/fan/state", f'On at {fan_duty_cycle * 100 / 4095:.2f}%')
                
                # send to database
                mongo_db_handler.insert_actuator_data(
                    "fan", fan_duty_cycle)

        # capture the image every 6 hours
        if (datetime.datetime.now() - last_time_captured).total_seconds() > IMAGE_CAP_INTERVAL * 3600:
            last_time_captured = datetime.datetime.now()
            # capture the image
            last_time_captured = datetime.datetime.now()
            image_path_cam0 = camera.capture_store_image(0)
            image_path_cam1 = camera.capture_store_image(1)
            i = 0
            for image_path in [image_path_cam0, image_path_cam1]:
                if image_path:
                    # upload the image to s3
                    s3_handler.upload_file(
                        image_path, os.path.basename(image_path))

                    # get the s3 url
                    s3_url = s3_handler.get_s3_url(os.path.basename(image_path))

                    if s3_url:
                        print(f"S3 URL: {s3_url}")
                        # insert the image url to the database
                        mongo_db_handler.insert_image_data("plant image", s3_url, i)
                        i += 1
                        # remove the image from local storage
                        camera.remove_image(image_path)                    
                    else:
                        print("Error getting S3 URL")                        
                    time.sleep(1)
                else:
                    print("Error capturing image")
        


if __name__ == "__main__":
    


    setpoints.set_control_thread_event("temperature", temperature_pause_event)
    setpoints.set_control_thread_event("light", light_pause_event)
    setpoints.set_control_thread_event("moisture", soil_pause_event)

    # create the threads
    app_thread = threading.Thread(target=app_task)
    temperature_thread = threading.Thread(target=temperature_sp_adjustment_task)
    light_thread = threading.Thread(target=light_sp_adjustment_task)
    soil_thread = threading.Thread(target=set_soil_moisture_setpoint_task)

    # start the threads
    app_thread.start()
    temperature_thread.start()
    light_thread.start()
    soil_thread.start()

    # wait for the threads to finish
    app_thread.join()
    serial_logger_thread.join()
    temperature_thread.join()
    light_thread.join()
    soil_thread.join()