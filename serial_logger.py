
import threading
import datetime
import os
import time

# Global dictionary to store the latest sensor and actuator data for display
latest_data = {
    "timestamp": "N/A",
    "temperature": "N/A", "humidity": "N/A",
    "soil_ph": "N/A", "soil_ec": "N/A", "soil_temp": "N/A", "soil_humidity": "N/A",
    "water_flow": "N/A", 
    "electricity_voltage": "N/A", "electricity_current": "N/A", "electricity_power": "N/A",
    "electricity_energy": "N/A", "electricity_frequency": "N/A", "electricity_pf": "N/A",
    "electricity_alarm": "N/A",
    "light_intensity": "N/A",
    "heater_dc": "N/A", "heater_fan_dc": "N/A", "light_strip_1_dc": "N/A",
    "light_strip_2_dc": "N/A", "water_pump_dc": "N/A", "fan_dc": "N/A"
}

# Lock for safely updating/reading latest_data 
data_lock = threading.Lock()

# Removed get_actuator_dc_safe helper function

def serial_logger_task(sensors, actuators, temp_sem, light_sem, soil_sem, flow_sem, electricity_sem):
    """Reads sensor/actuator data at intervals (read-only) using datetime, prints formatted block."""
    global latest_data
    
    # Initialize last read times to ensure the first read happens
    last_read_datetimes = {
        "temp_humidity": datetime.datetime.min,
        "soil": datetime.datetime.min,
        "flow": datetime.datetime.min,
        "electricity": datetime.datetime.min,
        "light": datetime.datetime.min,
        "actuators": datetime.datetime.min
    }
    
    # Define intervals using timedelta
    intervals = {
        "temp_humidity": datetime.timedelta(seconds=5),
        "soil": datetime.timedelta(seconds=3),
        "flow": datetime.timedelta(seconds=1),
        "electricity": datetime.timedelta(seconds=10),
        "light": datetime.timedelta(seconds=3),
        "actuators": datetime.timedelta(seconds=1)
    }

    while True:
        now = datetime.datetime.now()
        current_timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        local_latest_data = {}
        local_latest_data["timestamp"] = current_timestamp_str

        # --- Read Sensors/Actuators based on datetime intervals --- 

        # Temperature & Humidity (5s)
        if now >= last_read_datetimes["temp_humidity"] + intervals["temp_humidity"]:
            temp, humid = "N/A", "N/A"
            acquired = False
            if temp_sem:
                acquired = temp_sem.acquire(blocking=False)
            
            if acquired or not temp_sem:
                try:
                    temp = sensors.get_air_temperature_C()
                    humid = sensors.get_air_humidity()
                    temp = f"{temp:.1f}" if isinstance(temp, (int, float)) else "Read Error"
                    humid = f"{humid:.1f}" if isinstance(humid, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Temp/Hum: {e}")
                    temp, humid = "Exception", "Exception"
                finally:
                    if acquired:
                        temp_sem.release()
                last_read_datetimes["temp_humidity"] = now
            else: # Semaphore busy
                with data_lock:
                    temp = latest_data["temperature"]
                    humid = latest_data["humidity"]
            local_latest_data["temperature"] = temp
            local_latest_data["humidity"] = humid
        else:
            with data_lock:
                local_latest_data["temperature"] = latest_data["temperature"]
                local_latest_data["humidity"] = latest_data["humidity"]

        # Soil Sensors (3s)
        if now >= last_read_datetimes["soil"] + intervals["soil"]:
            soil_ph, soil_ec, soil_temp, soil_hum = "N/A", "N/A", "N/A", "N/A"
            acquired = False
            if soil_sem:
                acquired = soil_sem.acquire(blocking=False)
                
            if acquired or not soil_sem:
                try:
                    soil_ph = sensors.get_soil_ph()
                    soil_ec = sensors.get_soil_ec()
                    soil_temp = sensors.get_soil_temp()
                    soil_hum = sensors.get_soil_humidity()
                    soil_ph = f"{soil_ph:.1f}" if isinstance(soil_ph, (int, float)) else "Read Error"
                    soil_ec = f"{soil_ec:.1f}" if isinstance(soil_ec, (int, float)) else "Read Error"
                    soil_temp = f"{soil_temp:.1f}" if isinstance(soil_temp, (int, float)) else "Read Error"
                    soil_hum = f"{soil_hum:.1f}" if isinstance(soil_hum, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Soil: {e}")
                    soil_ph, soil_ec, soil_temp, soil_hum = "Ex", "Ex", "Ex", "Ex"
                finally:
                    if acquired:
                        soil_sem.release()
                last_read_datetimes["soil"] = now
            else: # Semaphore busy
                with data_lock:
                    soil_ph = latest_data["soil_ph"]
                    soil_ec = latest_data["soil_ec"]
                    soil_temp = latest_data["soil_temp"]
                    soil_hum = latest_data["soil_humidity"]
            local_latest_data["soil_ph"] = soil_ph
            local_latest_data["soil_ec"] = soil_ec
            local_latest_data["soil_temp"] = soil_temp
            local_latest_data["soil_humidity"] = soil_hum
        else:
             with data_lock:
                local_latest_data["soil_ph"] = latest_data["soil_ph"]
                local_latest_data["soil_ec"] = latest_data["soil_ec"]
                local_latest_data["soil_temp"] = latest_data["soil_temp"]
                local_latest_data["soil_humidity"] = latest_data["soil_humidity"]

        # Water Flow (1s)
        if now >= last_read_datetimes["flow"] + intervals["flow"]:
            flow = "N/A"
            acquired = False
            if flow_sem:
                 acquired = flow_sem.acquire(blocking=False)
                 
            if acquired or not flow_sem:
                try:
                    flow = sensors.get_water_flow()
                    flow = f"{flow:.2f}" if isinstance(flow, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Flow: {e}")
                    flow = "Exception"
                finally:
                    if acquired:
                        flow_sem.release()
                last_read_datetimes["flow"] = now
            else: # Semaphore busy
                with data_lock:
                    flow = latest_data["water_flow"]
            local_latest_data["water_flow"] = flow
        else:
            with data_lock:
                local_latest_data["water_flow"] = latest_data["water_flow"]

        # Electricity (10s) - Detailed Reading with Semaphore
        if now >= last_read_datetimes["electricity"] + intervals["electricity"]:
            elec_v, elec_c, elec_p, elec_e, elec_f, elec_pf, elec_a = ("N/A",)*7
            acquired = False
            if electricity_sem:
                acquired = electricity_sem.acquire(blocking=False)
            
            if acquired or not electricity_sem:
                try:
                    voltage, current, power, energy, frequency, power_factor, alarm = sensors.get_electricity_values()
                    elec_v = f"{voltage:.1f}" if isinstance(voltage, (int, float)) else "Read Error"
                    elec_c = f"{current:.2f}" if isinstance(current, (int, float)) else "Read Error"
                    elec_p = f"{power:.1f}" if isinstance(power, (int, float)) else "Read Error"
                    elec_e = f"{energy:.3f}" if isinstance(energy, (int, float)) else "Read Error"
                    elec_f = f"{frequency:.1f}" if isinstance(frequency, (int, float)) else "Read Error"
                    elec_pf = f"{power_factor:.2f}" if isinstance(power_factor, (int, float)) else "Read Error"
                    elec_a = str(alarm)
                except Exception as e:
                    print(f"Logger Error reading Electricity: {e}")
                    elec_v, elec_c, elec_p, elec_e, elec_f, elec_pf, elec_a = ("Exception",)*7
                finally:
                    if acquired:
                        electricity_sem.release()
                    last_read_datetimes["electricity"] = now
            else: # Semaphore busy
                with data_lock:
                    elec_v = latest_data["electricity_voltage"]
                    elec_c = latest_data["electricity_current"]
                    elec_p = latest_data["electricity_power"]
                    elec_e = latest_data["electricity_energy"]
                    elec_f = latest_data["electricity_frequency"]
                    elec_pf = latest_data["electricity_pf"]
                    elec_a = latest_data["electricity_alarm"]
            
            # Store individually
            local_latest_data["electricity_voltage"] = elec_v
            local_latest_data["electricity_current"] = elec_c
            local_latest_data["electricity_power"] = elec_p
            local_latest_data["electricity_energy"] = elec_e
            local_latest_data["electricity_frequency"] = elec_f
            local_latest_data["electricity_pf"] = elec_pf
            local_latest_data["electricity_alarm"] = elec_a
        else:
            # Use last known values if not time to read
            with data_lock:
                local_latest_data["electricity_voltage"] = latest_data["electricity_voltage"]
                local_latest_data["electricity_current"] = latest_data["electricity_current"]
                local_latest_data["electricity_power"] = latest_data["electricity_power"]
                local_latest_data["electricity_energy"] = latest_data["electricity_energy"]
                local_latest_data["electricity_frequency"] = latest_data["electricity_frequency"]
                local_latest_data["electricity_pf"] = latest_data["electricity_pf"]
                local_latest_data["electricity_alarm"] = latest_data["electricity_alarm"]

        # Light Intensity (3s)
        if now >= last_read_datetimes["light"] + intervals["light"]:
            light = "N/A"
            acquired = False
            if light_sem:
                acquired = light_sem.acquire(blocking=False)
                
            if acquired or not light_sem:
                try:
                    light = sensors.get_light_intensity()
                    light = f"{light:.0f}" if isinstance(light, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Light: {e}")
                    light = "Exception"
                finally:
                    if acquired:
                        light_sem.release()
                last_read_datetimes["light"] = now
            else: # Semaphore busy
                with data_lock:
                    light = latest_data["light_intensity"]
            local_latest_data["light_intensity"] = light
        else:
            with data_lock:
                local_latest_data["light_intensity"] = latest_data["light_intensity"]

        # Actuator Duty Cycles (1s) - Direct Try/Except
        if now >= last_read_datetimes["actuators"] + intervals["actuators"]:
            # Heater DC
            try:
                local_latest_data["heater_dc"] = actuators.get_heater_duty_cycle()
            except AttributeError:
                 local_latest_data["heater_dc"] = "Not Impl."
            except Exception as e:
                print(f"Logger Error reading Heater DC: {e}")
                local_latest_data["heater_dc"] = "Error"
            # Heater Fan DC
            try:
                local_latest_data["heater_fan_dc"] = actuators.get_heater_fan_duty_cycle()
            except AttributeError:
                 local_latest_data["heater_fan_dc"] = "Not Impl."
            except Exception as e:
                print(f"Logger Error reading Heater Fan DC: {e}")
                local_latest_data["heater_fan_dc"] = "Error"
            # Light Strip 1 DC
            try:
                local_latest_data["light_strip_1_dc"] = actuators.get_light_strip_1_duty_cycle()
            except AttributeError:
                 local_latest_data["light_strip_1_dc"] = "Not Impl."
            except Exception as e:
                print(f"Logger Error reading Light 1 DC: {e}")
                local_latest_data["light_strip_1_dc"] = "Error"
            # Light Strip 2 DC
            try:
                local_latest_data["light_strip_2_dc"] = actuators.get_light_strip_2_duty_cycle()
            except AttributeError:
                 local_latest_data["light_strip_2_dc"] = "Not Impl."
            except Exception as e:
                print(f"Logger Error reading Light 2 DC: {e}")
                local_latest_data["light_strip_2_dc"] = "Error"
            # Water Pump DC
            try:
                local_latest_data["water_pump_dc"] = actuators.get_water_pump_duty_cycle()
            except AttributeError:
                 local_latest_data["water_pump_dc"] = "Not Impl."
            except Exception as e:
                print(f"Logger Error reading Pump DC: {e}")
                local_latest_data["water_pump_dc"] = "Error"
            # Fan DC
            try:
                local_latest_data["fan_dc"] = actuators.get_fan_duty_cycle()
            except AttributeError:
                 local_latest_data["fan_dc"] = "Not Impl."
            except Exception as e:
                print(f"Logger Error reading Fan DC: {e}")
                local_latest_data["fan_dc"] = "Error"
                
            last_read_datetimes["actuators"] = now
        else:
            # Use last known values if not time to read
            with data_lock:
                local_latest_data["heater_dc"] = latest_data["heater_dc"]
                local_latest_data["heater_fan_dc"] = latest_data["heater_fan_dc"]
                local_latest_data["light_strip_1_dc"] = latest_data["light_strip_1_dc"]
                local_latest_data["light_strip_2_dc"] = latest_data["light_strip_2_dc"]
                local_latest_data["water_pump_dc"] = latest_data["water_pump_dc"]
                local_latest_data["fan_dc"] = latest_data["fan_dc"]

        # Update global state safely
        with data_lock:
            latest_data.update(local_latest_data)

        # --- Formatting --- 
        sensor_col_width = 18
        value_col_width = 18
        total_width = sensor_col_width + value_col_width + 3

        output = []
        sep_line = '+' + '-' * (total_width - 2) + '+'
        title_line = '|' + "Greenhouse Serial Monitor (Read-Only)".center(total_width - 2) + '|'
        timestamp_line = '|' + f" Timestamp: {local_latest_data['timestamp']} ".ljust(total_width - 2) + '|'
        header_sep = '+' + '-' * sensor_col_width + '+' + '-' * value_col_width + '+'
        sensor_header = '|' + " Sensor".ljust(sensor_col_width) + '|' + " Value".ljust(value_col_width) + '|'
        actuator_header = '|' + " Actuator".ljust(sensor_col_width) + '|' + " Duty Cycle (Raw%)".ljust(value_col_width) + '|'

        output.append(sep_line)
        output.append(title_line)
        output.append(sep_line)
        output.append(timestamp_line)
        output.append(header_sep)
        output.append(sensor_header)
        output.append(header_sep)

        def format_value(value, unit):
            is_numeric = isinstance(value, (int, float))
            val_str = f"{value:.1f}" if isinstance(value, float) and unit != "kWh" and unit != "A" and unit != "" else str(value)
            if isinstance(value, float) and unit == "kWh": val_str = f"{value:.3f}"
            if isinstance(value, float) and unit == "A": val_str = f"{value:.2f}"
            if isinstance(value, float) and unit == "PF": val_str = f"{value:.2f}"
            return f"{val_str} {unit}" if is_numeric else str(value)

        sensors_to_print = [
            ("Temp (Air)", local_latest_data['temperature'], "C"),
            ("Humidity (Air)", local_latest_data['humidity'], "%"),
            ("Light Intensity", local_latest_data['light_intensity'], "Lux"),
            ("Soil pH", local_latest_data['soil_ph'], "pH"),
            ("Soil EC", local_latest_data['soil_ec'], "uS/cm"),
            ("Soil Temp", local_latest_data['soil_temp'], "C"),
            ("Soil Humidity", local_latest_data['soil_humidity'], "%"),
            ("Water Flow", local_latest_data['water_flow'], "L/min"),
            ("Voltage", local_latest_data['electricity_voltage'], "V"),
            ("Current", local_latest_data['electricity_current'], "A"),
            ("Power", local_latest_data['electricity_power'], "W"),
            ("Energy", local_latest_data['electricity_energy'], "kWh"),
            ("Frequency", local_latest_data['electricity_frequency'], "Hz"),
            ("Power Factor", local_latest_data['electricity_pf'], "PF"),
            ("Alarm Status", local_latest_data['electricity_alarm'], "")
        ]
        for name, value, unit in sensors_to_print:
            # Re-check type for formatting as value might be string like "Error"
            current_value = local_latest_data.get(name.lower().replace(" ", "_").replace("(","").replace(")",""), value) # Get potentially updated value
            val_str = format_value(current_value, unit)
            output.append('|' + f" {name}".ljust(sensor_col_width) + '|' + f" {val_str}".ljust(value_col_width) + '|')

        output.append(header_sep)
        output.append(actuator_header)
        output.append(header_sep)

        max_dc = 4095
        actuators_to_print = [
            ("Heater", local_latest_data['heater_dc']),
            ("Heater Fan", local_latest_data['heater_fan_dc']),
            ("Light Strip 1", local_latest_data['light_strip_1_dc']),
            ("Light Strip 2", local_latest_data['light_strip_2_dc']),
            ("Water Pump", local_latest_data['water_pump_dc']),
            ("Cooling Fan", local_latest_data['fan_dc'])
        ]
        for name, dc in actuators_to_print:
            if isinstance(dc, (int, float)):
                dc_perc = (dc / max_dc * 100) if max_dc > 0 else 0
                val_str = f"{dc:<4} ({dc_perc:.1f}%)"
            else:
                val_str = str(dc)
            output.append('|' + f" {name}".ljust(sensor_col_width) + '|' + f" {val_str}".ljust(value_col_width) + '|')

        output.append(sep_line)

        os.system('clear')
        print("\n".join(output))

        time.sleep(1)