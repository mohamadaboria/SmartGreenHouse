# --- Simplified Datetime-Based Read-Only Serial Logger Task (Units Fixed) --- 

import os
import time
import datetime
import threading

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

def serial_logger_task(sensors, actuators, temp_sem, light_sem, soil_sem, flow_sem, electricity_sem):
    """Reads sensor/actuator data at intervals (read-only) using datetime, prints formatted block."""
    global latest_data
    
    last_read_datetimes = {
        "temp_humidity": datetime.datetime.min,
        "soil": datetime.datetime.min,
        "flow": datetime.datetime.min,
        "electricity": datetime.datetime.min,
        "light": datetime.datetime.min,
        "actuators": datetime.datetime.min
    }
    
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
                    # Store raw numeric or error string
                    local_latest_data["temperature"] = temp if isinstance(temp, (int, float)) else "Read Error"
                    local_latest_data["humidity"] = humid if isinstance(humid, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Temp/Hum: {e}")
                    local_latest_data["temperature"] = "Exception"
                    local_latest_data["humidity"] = "Exception"
                finally:
                    if acquired:
                        temp_sem.release()
                last_read_datetimes["temp_humidity"] = now
            else: # Semaphore busy
                with data_lock:
                    local_latest_data["temperature"] = latest_data["temperature"]
                    local_latest_data["humidity"] = latest_data["humidity"]
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
                    soil_ph, soil_ec, soil_hum, soil_temp = sensors.get_soil_values()
                    local_latest_data["soil_ph"] = soil_ph if isinstance(soil_ph, (int, float)) else "Read Error"
                    local_latest_data["soil_ec"] = soil_ec if isinstance(soil_ec, (int, float)) else "Read Error"
                    local_latest_data["soil_temp"] = soil_temp if isinstance(soil_temp, (int, float)) else "Read Error"
                    local_latest_data["soil_humidity"] = soil_hum if isinstance(soil_hum, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Soil: {e}")
                    local_latest_data["soil_ph"] = "Ex"
                    local_latest_data["soil_ec"] = "Ex"
                    local_latest_data["soil_temp"] = "Ex"
                    local_latest_data["soil_humidity"] = "Ex"
                finally:
                    if acquired:
                        soil_sem.release()
                last_read_datetimes["soil"] = now
            else: # Semaphore busy
                with data_lock:
                    local_latest_data["soil_ph"] = latest_data["soil_ph"]
                    local_latest_data["soil_ec"] = latest_data["soil_ec"]
                    local_latest_data["soil_temp"] = latest_data["soil_temp"]
                    local_latest_data["soil_humidity"] = latest_data["soil_humidity"]
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
                    flow = sensors.get_water_flow_rate()
                    local_latest_data["water_flow"] = flow if isinstance(flow, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Flow: {e}")
                    local_latest_data["water_flow"] = "Exception"
                finally:
                    if acquired:
                        flow_sem.release()
                last_read_datetimes["flow"] = now
            else: # Semaphore busy
                with data_lock:
                    local_latest_data["water_flow"] = latest_data["water_flow"]
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
                    if hasattr(sensors, 'get_electricity_values'):
                        voltage, current, power, energy, frequency, power_factor, alarm = sensors.get_electricity_values()
                        local_latest_data["electricity_voltage"] = voltage if isinstance(voltage, (int, float)) else "Read Error"
                        local_latest_data["electricity_current"] = current if isinstance(current, (int, float)) else "Read Error"
                        local_latest_data["electricity_power"] = power if isinstance(power, (int, float)) else "Read Error"
                        local_latest_data["electricity_energy"] = energy if isinstance(energy, (int, float)) else "Read Error"
                        local_latest_data["electricity_frequency"] = frequency if isinstance(frequency, (int, float)) else "Read Error"
                        local_latest_data["electricity_pf"] = power_factor if isinstance(power_factor, (int, float)) else "Read Error"
                        local_latest_data["electricity_alarm"] = str(alarm) # Alarm might not be numeric
                    else:
                        local_latest_data["electricity_voltage"] = "Not Impl."
                        local_latest_data["electricity_current"] = "Not Impl."
                        local_latest_data["electricity_power"] = "Not Impl."
                        local_latest_data["electricity_energy"] = "Not Impl."
                        local_latest_data["electricity_frequency"] = "Not Impl."
                        local_latest_data["electricity_pf"] = "Not Impl."
                        local_latest_data["electricity_alarm"] = "Not Impl."
                except Exception as e:
                    print(f"Logger Error reading Electricity: {e}")
                    local_latest_data["electricity_voltage"] = "Exception"
                    local_latest_data["electricity_current"] = "Exception"
                    local_latest_data["electricity_power"] = "Exception"
                    local_latest_data["electricity_energy"] = "Exception"
                    local_latest_data["electricity_frequency"] = "Exception"
                    local_latest_data["electricity_pf"] = "Exception"
                    local_latest_data["electricity_alarm"] = "Exception"
                finally:
                    if acquired:
                        electricity_sem.release()
                    last_read_datetimes["electricity"] = now
            else: # Semaphore busy
                with data_lock:
                    local_latest_data["electricity_voltage"] = latest_data["electricity_voltage"]
                    local_latest_data["electricity_current"] = latest_data["electricity_current"]
                    local_latest_data["electricity_power"] = latest_data["electricity_power"]
                    local_latest_data["electricity_energy"] = latest_data["electricity_energy"]
                    local_latest_data["electricity_frequency"] = latest_data["electricity_frequency"]
                    local_latest_data["electricity_pf"] = latest_data["electricity_pf"]
                    local_latest_data["electricity_alarm"] = latest_data["electricity_alarm"]
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
                    local_latest_data["light_intensity"] = light if isinstance(light, (int, float)) else "Read Error"
                except Exception as e:
                    print(f"Logger Error reading Light: {e}")
                    local_latest_data["light_intensity"] = "Exception"
                finally:
                    if acquired:
                        light_sem.release()
                last_read_datetimes["light"] = now
            else: # Semaphore busy
                with data_lock:
                    local_latest_data["light_intensity"] = latest_data["light_intensity"]
        else:
            with data_lock:
                local_latest_data["light_intensity"] = latest_data["light_intensity"]

        # Actuator Duty Cycles (1s) - Direct Try/Except
        if now >= last_read_datetimes["actuators"] + intervals["actuators"]:
            # Read each actuator, store raw value or error string
            try:
                local_latest_data["heater_dc"] = actuators.get_heater_duty_cycle()
            except AttributeError: local_latest_data["heater_dc"] = "Not Impl."
            except Exception as e: print(f"Logger Error reading Heater DC: {e}"); local_latest_data["heater_dc"] = "Error"
            
            try:
                local_latest_data["heater_fan_dc"] = actuators.get_heater_fan_duty_cycle()
            except AttributeError: local_latest_data["heater_fan_dc"] = "Not Impl."
            except Exception as e: print(f"Logger Error reading Heater Fan DC: {e}"); local_latest_data["heater_fan_dc"] = "Error"

            try:
                local_latest_data["light_strip_1_dc"] = actuators.get_light_strip_1_duty_cycle()
            except AttributeError: local_latest_data["light_strip_1_dc"] = "Not Impl."
            except Exception as e: print(f"Logger Error reading Light 1 DC: {e}"); local_latest_data["light_strip_1_dc"] = "Error"

            try:
                local_latest_data["light_strip_2_dc"] = actuators.get_light_strip_2_duty_cycle()
            except AttributeError: local_latest_data["light_strip_2_dc"] = "Not Impl."
            except Exception as e: print(f"Logger Error reading Light 2 DC: {e}"); local_latest_data["light_strip_2_dc"] = "Error"

            try:
                local_latest_data["water_pump_dc"] = actuators.get_water_pump_duty_cycle()
            except AttributeError: local_latest_data["water_pump_dc"] = "Not Impl."
            except Exception as e: print(f"Logger Error reading Pump DC: {e}"); local_latest_data["water_pump_dc"] = "Error"

            try:
                local_latest_data["fan_dc"] = actuators.get_fan_duty_cycle()
            except AttributeError: local_latest_data["fan_dc"] = "Not Impl."
            except Exception as e: print(f"Logger Error reading Fan DC: {e}"); local_latest_data["fan_dc"] = "Error"
                
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
        value_col_width = 18 # Adjust if needed for units
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

        # Corrected format_value function
        def format_value(value, unit):
            if isinstance(value, (int, float)):
                if unit == "kWh": formatted_val = f"{value:.3f}"
                elif unit == "A" or unit == "PF" or unit == "L/min": formatted_val = f"{value:.2f}"
                elif unit == "Lux": formatted_val = f"{value:.0f}"
                elif isinstance(value, float): formatted_val = f"{value:.1f}"
                else: formatted_val = str(value)
                # Append unit only if unit string is not empty
                return f"{formatted_val} {unit}" if unit else formatted_val
            else:
                # Return non-numeric values (like "Error", "N/A") as is
                return str(value)

        # Define sensors with their display name, data key, and unit
        sensors_to_print = [
            ("Temp (Air)", "temperature", "C"),
            ("Humidity (Air)", "humidity", "%"),
            ("Light Intensity", "light_intensity", "Lux"),
            ("Soil pH", "soil_ph", "pH"),
            ("Soil EC", "soil_ec", "uS/cm"),
            ("Soil Temp", "soil_temp", "C"),
            ("Soil Humidity", "soil_humidity", "%"),
            ("Water Flow", "water_flow", "L/min"),
            ("Voltage", "electricity_voltage", "V"),
            ("Current", "electricity_current", "A"),
            ("Power", "electricity_power", "W"),
            ("Energy", "electricity_energy", "Wh"),
            ("Frequency", "electricity_frequency", "Hz"),
            ("Power Factor", "electricity_pf", "PF"), # Using PF as unit helps formatting
            ("Alarm Status", "electricity_alarm", "") # No unit for alarm
        ]
        
        # Iterate and format sensor values
        for name, data_key, unit in sensors_to_print:
            current_value = local_latest_data.get(data_key, "N/A") # Get value using key
            val_str = format_value(current_value, unit) # Format the value
            output.append('|' + f" {name}".ljust(sensor_col_width) + '|' + f" {val_str}".ljust(value_col_width) + '|')

        output.append(header_sep)
        output.append(actuator_header)
        output.append(header_sep)

        max_dc = 4095
        actuators_to_print = [
            ("Heater", "heater_dc"),
            ("Heater Fan", "heater_fan_dc"),
            ("Light Strip 1", "light_strip_1_dc"),
            ("Light Strip 2", "light_strip_2_dc"),
            ("Water Pump", "water_pump_dc"),
            ("Cooling Fan", "fan_dc")
        ]
        
        # Iterate and format actuator values
        for name, data_key in actuators_to_print:
            dc = local_latest_data.get(data_key, "N/A") # Get value using key
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