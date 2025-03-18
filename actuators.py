import gpiod
import os
import numpy as np


class GH_Actuators:
    def __init__(self, relay_logic):
        self.__relay_logic = relay_logic

    def set_heater_pins(self, heater_pin, heater_fan_pin):
        self.__heater_pin = heater_pin
        self.__heater_fan_pin = heater_fan_pin

        self.chip = gpiod.chip('gpiochip4')
        self.__heater_pin = self.chip.get_line(heater_pin)
        # self.__heater_fan_pin = self.chip.get_line(heater_fan_pin)

        config = gpiod.line_request()
        config.consumer = "Heater"
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT

        self.__heater_pin.request(config=config, default_val=0)
        # self.__heater_fan_pin.request(config=config, default_val=0)

    def set_light_pins(self, light_pin):
        self.__light_pin = light_pin
        self.chip = gpiod.chip('gpiochip4')
        self.__light_pin = self.chip.get_line(light_pin)

        config = gpiod.line_request()
        config.consumer = "Light"
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT

        self.__light_pin.request(config=config, default_val=0)

    def set_water_pump_pins(self, water_pump_pin):
        self.__water_pump_pin = water_pump_pin
        self.chip = gpiod.chip('gpiochip4')
        self.__water_pump_pin = self.chip.get_line(water_pump_pin)

        config = gpiod.line_request()
        config.consumer = "Water Pump"
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT

        self.__water_pump_pin.request(config=config, default_val=0)

    def set_fan_pins(self, fan_pin):
        self.__fan_pin = fan_pin
        self.chip = gpiod.chip('gpiochip4')
        self.__fan_pin = self.chip.get_line(fan_pin)

        config = gpiod.line_request()
        config.consumer = "Fan"
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT

        self.__fan_pin.request(config=config, default_val=0)

    def turn_on_heater(self):
        self.__heater_pin.set_value(self.__relay_logic)
        # self.__heater_fan_pin.set_value(self.__relay_logic)

    def turn_off_heater(self):
        self.__heater_pin.set_value(not self.__relay_logic)
        # self.__heater_fan_pin.set_value(not self.__relay_logic)

    def turn_on_light(self):
        self.__light_pin.set_value(self.__relay_logic)

    def turn_off_light(self):
        self.__light_pin.set_value(not self.__relay_logic)

    def turn_on_water_pump(self):
        self.__water_pump_pin.set_value(self.__relay_logic)

    def turn_off_water_pump(self):
        self.__water_pump_pin.set_value(not self.__relay_logic)

    def turn_on_fan(self):
        self.__fan_pin.set_value(self.__relay_logic)

    def turn_off_fan(self):
        self.__fan_pin.set_value(not self.__relay_logic)        