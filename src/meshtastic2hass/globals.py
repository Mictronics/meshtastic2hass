# This file is part of Meshtastic to Home Assistant (Hass)
#
# Copyright (c) 2024 Michael Wolf <michael@mictronics.de>
#
# meshtastic2hass is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# meshtastic2hass is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with meshtastic2hass. If not, see http://www.gnu.org/licenses/.
#
class Globals:
    """Globals class is a Singleton."""

    __instance = None

    @staticmethod
    def getInstance():
        """Get an instance of the Globals class."""
        if Globals.__instance is None:
            Globals()
        return Globals.__instance

    def __init__(self):
        """Constructor for the Globals CLass"""
        if Globals.__instance is not None:
            raise Exception("This class is a singleton")
        else:
            Globals.__instance = self
        self.args = None
        self.parser = None
        self.loop = None
        self.mqtt = None
        # Home Assistant sensor configuration send via MQTT.
        self.mqttSensors = [
            dict(
                id="battery_voltage",
                name="Battery Voltage",
                state_topic="device",
                device_class="voltage",
                unit="V",
                property="voltage",
                type="float",
            ),
            dict(
                id="battery_percent",
                name="Battery Level",
                state_topic="device",
                device_class="battery",
                unit="%",
                property="batteryLevel",
                type="float",
            ),
            dict(
                id="chutil",
                name="Channel Util",
                state_topic="device",
                device_class=None,
                unit="%",
                property="channelUtilization",
                type="float",
            ),
            dict(
                id="airutiltx",
                name="Air Util Tx",
                state_topic="device",
                device_class=None,
                unit="%",
                property="channelUtilization",
                type="float",
            ),
            dict(
                id="temperature",
                name="Temperature",
                state_topic="environment",
                device_class="temperature",
                unit="°C",
                property="temperature",
                type="float",
            ),
            dict(
                id="humidity",
                name="Humidity",
                state_topic="environment",
                device_class="humidity",
                unit="%",
                property="relativeHumidity",
                type="float",
            ),
            dict(
                id="pressure",
                name="Pressure",
                state_topic="environment",
                device_class="atmospheric_pressure",
                unit="hPa",
                property="barometricPressure",
                type="float",
            ),
            dict(
                id="voltage",
                name="Voltage",
                state_topic="environment",
                device_class="voltage",
                unit="V",
                property="voltage",
                type="float",
            ),
            dict(
                id="current",
                name="Current",
                state_topic="environment",
                device_class="current",
                unit="mA",
                property="current",
                type="float",
            ),
            dict(
                id="rssi",
                name="RSSI",
                state_topic="device",
                device_class="signal_strength",
                unit="dBm",
                property="rssi",
                type="int",
            ),
            dict(
                id="snr",
                name="SNR",
                state_topic="device",
                device_class=None,
                unit=None,
                property="snr",
                type="float",
            ),
            dict(
                id="ch1_voltage",
                name="Voltage Sensor 1",
                state_topic="power",
                device_class="voltage",
                unit="V",
                property="ch1Voltage",
                type="float",
            ),
            dict(
                id="ch1_current",
                name="Current Sensor 1",
                state_topic="power",
                device_class="current",
                unit="mA",
                property="ch1Current",
                type="float",
            ),
            dict(
                id="ch2_voltage",
                name="Voltage Sensor 2",
                state_topic="power",
                device_class="voltage",
                unit="V",
                property="ch2Voltage",
                type="float",
            ),
            dict(
                id="ch2_current",
                name="Current Sensor 2",
                state_topic="power",
                device_class="current",
                unit="mA",
                property="ch2Current",
                type="float",
            ),
            dict(
                id="ch3_voltage",
                name="Voltage Sensor 3",
                state_topic="power",
                device_class="voltage",
                unit="V",
                property="ch3Voltage",
                type="float",
            ),
            dict(
                id="ch3_current",
                name="Current Sensor 3",
                state_topic="power",
                device_class="current",
                unit="mA",
                property="ch3Current",
                type="float",
            ),
        ]
        self.mqttTopicPrefix = "msh/2/json"

    def reset(self):
        """Reset all of our globals. If you add a member, add it to this method, too."""
        self.args = None
        self.parser = None
        self.loop = None
        self.mqtt = None
        self.mqttTopicPrefix = "msh/2/json"

    # setters
    def setArgs(self, args):
        """Set the args"""
        self.args = args

    def setParser(self, parser):
        """Set the parser"""
        self.parser = parser

    def setLoop(self, loop):
        """Set the loop"""
        self.loop = loop

    def setMQTT(self, mqtt):
        """Set the MQTT client"""
        self.mqtt = mqtt

    def setTopicPrefix(self, prefix):
        """Set the MQTT topic prefix"""
        self.mqttTopicPrefix = prefix

    # getters
    def getArgs(self):
        """Get args"""
        return self.args

    def getParser(self):
        """Get parser"""
        return self.parser

    def getLoop(self):
        """Get the loop"""
        return self.loop

    def getMQTT(self):
        """Get the MQTT client"""
        return self.mqtt

    def getSensors(self):
        """Get the MQTT sensor configuration"""
        return self.mqttSensors

    def getTopicPrefix(self):
        """Get the MQTT topic prefix"""
        return self.mqttTopicPrefix
