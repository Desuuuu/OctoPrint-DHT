# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from flask import make_response
from octoprint.util import RepeatedTimer

import Adafruit_DHT

DEFAULT_ENABLE = False
DEFAULT_SENSOR_TYPE = "dht22"
DEFAULT_DATA_PIN = 4
DEFAULT_REFRESH_INTERVAL = 60
DEFAULT_DECIMALS = 1
DEFAULT_MAX_HUMIDITY = 15
DEFAULT_MAX_TEMPERATURE = 50

class DHTSensorPlugin(octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.SimpleApiPlugin,
                      octoprint.plugin.ReloadNeedingPlugin):

	def __init__(self):
		self.enable = False
		self.sensorType = ""
		self.dataPin = 0
		self.refreshInterval = 0
		self.decimals = 0
		self.maxHumidity = 0
		self.maxTemperature = 0

		self.humidity = -1
		self.temperature = -1

		self._updateTimer = None

	def initialize(self):
		self._load_settings()

		self._updateTimer = RepeatedTimer(self.refreshInterval,
		                                  self._update_temperature,
		                                  run_first = True)

		self._updateTimer.start()

	def _load_settings(self):
		self.enable = self._settings.get_boolean(["enable"])
		self.sensorType = self._settings.get(["sensorType"])
		self.dataPin = self._settings.get_int(["dataPin"])
		self.refreshInterval = self._settings.get_int(["refreshInterval"])
		self.decimals = self._settings.get_int(["decimals"])
		self.maxHumidity = self._settings.get_int(["maxHumidity"])
		self.maxTemperature = self._settings.get_int(["maxTemperature"])

		if self.sensorType not in ["dht11", "dht22"]:
			self._logger.warning("Invalid sensorType: %s", self.sensorType)

			self.sensorType = DEFAULT_SENSOR_TYPE

		if self.dataPin < 0 or self.dataPin > 40:
			self._logger.warning("Invalid dataPin: %s", self.dataPin)

			self.dataPin = DEFAULT_DATA_PIN

		if self.refreshInterval < 10 or self.refreshInterval > 86400:
			self._logger.warning("Invalid refreshInterval: %s", self.refreshInterval)

			self.refreshInterval = DEFAULT_REFRESH_INTERVAL

		if self.decimals < 0 or self.decimals > 3:
			self._logger.warning("Invalid decimals: %s", self.decimals)

			self.decimals = DEFAULT_DECIMALS

		if self.maxHumidity < 0 or self.maxHumidity > 100:
			self._logger.warning("Invalid maxHumidity: %s", self.maxHumidity)

			self.maxHumidity = DEFAULT_MAX_HUMIDITY

		if self.maxTemperature < 0 or self.maxTemperature > 100:
			self._logger.warning("Invalid maxTemperature: %s", self.maxTemperature)

			self.maxTemperature = DEFAULT_MAX_TEMPERATURE

		self._logger.debug("enable: %s", self.enable)
		self._logger.debug("sensorType: %s", self.sensorType)
		self._logger.debug("dataPin: %s", self.dataPin)
		self._logger.debug("refreshInterval: %s", self.refreshInterval)
		self._logger.debug("decimals: %s", self.decimals)
		self._logger.debug("maxHumidity: %s", self.maxHumidity)
		self._logger.debug("maxTemperature: %s", self.maxTemperature)

	def _update_temperature(self):
		if not self.enable:
			return

		try:
			if self.sensorType == "dht11":
				humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11,
				                                                self.dataPin,
				                                                5)
			elif self.sensorType == "dht22":
				humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22,
				                                                self.dataPin,
				                                                5)
			else:
				return
		except Exception as err:
			self._logger.warning("Failed to read sensor: %s", err)

			humidity = -1
			temperature = -1

		self._logger.debug("Retrieved sensor values: %s | %s", humidity, temperature)

		if (humidity is None or temperature is None or
			humidity < 0 or temperature < 0 or
			humidity > 100 or temperature > 100):
			self._logger.warning("Invalid sensor data: %s | %s", humidity, temperature)

			humidity = -1
			temperature = -1

		self.humidity = int(round(humidity * pow(10, self.decimals)))
		self.temperature = int(round(temperature * pow(10, self.decimals)))

		self._plugin_manager.send_plugin_message(self._identifier, dict(
			humidity = self.humidity,
			temperature = self.temperature,
			decimals = self.decimals
		))

	#~~ TemplatePlugin

	def get_template_configs(self):
		return [
			dict(
				type = "sidebar",
				name = "DHT Sensor",
				custom_bindings = False,
				icon = "archive",
				template_header = "dhtsensor_sidebar_header.jinja2"
			),
			dict(
				type = "settings",
				custom_bindings = False
			)
		]

	#~~ AssetPlugin

	def get_assets(self):
		return dict(
			js = [
				"js/decimal.min.js",
				"js/dhtsensor.js"
			],
			css = [
				"css/dhtsensor.css"
			]
		)

	#~~ SettingsPlugin

	def get_settings_defaults(self):
		return dict(
			enable = DEFAULT_ENABLE,
			sensorType = DEFAULT_SENSOR_TYPE,
			dataPin = DEFAULT_DATA_PIN,
			refreshInterval = DEFAULT_REFRESH_INTERVAL,
			decimals = DEFAULT_DECIMALS,
			maxHumidity = DEFAULT_MAX_HUMIDITY,
			maxTemperature = DEFAULT_MAX_TEMPERATURE
		)

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		self._load_settings()

		self._plugin_manager.send_plugin_message(self._identifier, dict(
			humidity = -1,
			temperature = -1,
			enable = self.enable,
			decimals = 0,
			maxHumidity = self.maxHumidity,
			maxTemperature = self.maxTemperature
		))

		if self._updateTimer is not None:
			self._updateTimer.cancel()

		self._updateTimer = RepeatedTimer(self.refreshInterval,
		                                  self._update_temperature,
		                                  run_first = True)

		self._updateTimer.start()

	#~~ SimpleApiPlugin

	def get_api_commands(self):
		return dict(
			refresh=[]
		)

	def on_api_command(self, command, data):
		if command == "refresh":
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				enable = self.enable,
				maxHumidity = self.maxHumidity,
				maxTemperature = self.maxTemperature
			))

			self._update_temperature()
		else:
			return make_response("Not Found", 404)

	def on_api_get(self, request):
		return make_response("Not Found", 404)

__plugin_name__ = "DHT Sensor"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = DHTSensorPlugin()
