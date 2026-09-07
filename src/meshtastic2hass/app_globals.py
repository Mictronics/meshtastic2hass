# This file is part of Meshtastic to Home Assistant (Hass)
#
# Copyright (c) 2025 Michael Wolf <michael@mictronics.de>
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
"""Process-wide shared state. A module is already a singleton, so callers
just `import app_globals as g` and read/write attributes (e.g. `g.mqtt`).

Named app_globals, not globals, because `globals` collides with the
third-party PyPI package of that name pulled in as a dependency."""

args = None
parser = None
loop = None
mqtt = None
interface = None
specialChars = r"[!]"
topicPrefix = "msh/2/json"
channelList = []
filterNodes = []

# Home Assistant sensor configuration sent via MQTT.
sensors = [
    dict(
        id="battery_voltage",
        name="Battery Voltage",
        state_topic="device",
        state_class="measurement",
        device_class="voltage",
        unit="V",
        property="voltage",
        type="float",
    ),
    dict(
        id="battery_percent",
        name="Battery Level",
        state_topic="device",
        state_class="measurement",
        device_class="battery",
        unit="%",
        property="batteryLevel",
        type="float",
    ),
    dict(
        id="chutil",
        name="Channel Util",
        state_topic="device",
        state_class="measurement",
        device_class=None,
        unit="%",
        property="channelUtilization",
        type="float",
    ),
    dict(
        id="airutiltx",
        name="Air Util Tx",
        state_topic="device",
        state_class="measurement",
        device_class=None,
        unit="%",
        property="airUtilTx",
        type="float",
    ),
    dict(
        id="temperature",
        name="Temperature",
        state_topic="environment",
        state_class="measurement",
        device_class="temperature",
        unit="°C",
        property="temperature",
        type="float",
    ),
    dict(
        id="humidity",
        name="Humidity",
        state_topic="environment",
        state_class="measurement",
        device_class="humidity",
        unit="%",
        property="relativeHumidity",
        type="float",
    ),
    dict(
        id="pressure",
        name="Pressure",
        state_topic="environment",
        state_class="measurement",
        device_class="atmospheric_pressure",
        unit="hPa",
        property="barometricPressure",
        type="float",
    ),
    dict(
        id="iaq",
        name="AQI",
        state_topic="environment",
        state_class="measurement",
        device_class="aqi",
        unit=None,
        property="iaq",
        type="int",
    ),
    dict(
        id="voltage",
        name="Voltage",
        state_topic="environment",
        state_class="measurement",
        device_class="voltage",
        unit="V",
        property="voltage",
        type="float",
    ),
    dict(
        id="current",
        name="Current",
        state_topic="environment",
        state_class="measurement",
        device_class="current",
        unit="mA",
        property="current",
        type="float",
    ),
    dict(
        id="rssi",
        name="RSSI",
        state_topic="device",
        state_class="measurement",
        device_class="signal_strength",
        unit="dBm",
        property="rssi",
        type="int",
    ),
    dict(
        id="snr",
        name="SNR",
        state_topic="device",
        state_class="measurement",
        device_class=None,
        unit=None,
        property="snr",
        type="float",
    ),
    dict(
        id="uptime",
        name="Uptime",
        state_topic="device",
        state_class="total_increasing",
        device_class="duration",
        unit="s",
        property="uptimeSeconds",
        type="int",
    ),
    dict(
        id="hopdistance",
        name="Hop Distance",
        state_topic="device",
        state_class="measurement",
        device_class=None,
        unit=None,
        property="hopDistance",
        type="int",
    ),
    dict(
        id="ch1_voltage",
        name="Voltage Sensor 1",
        state_topic="power",
        state_class="measurement",
        device_class="voltage",
        unit="V",
        property="ch1Voltage",
        type="float",
    ),
    dict(
        id="ch1_current",
        name="Current Sensor 1",
        state_topic="power",
        state_class="measurement",
        device_class="current",
        unit="mA",
        property="ch1Current",
        type="float",
    ),
    dict(
        id="ch2_voltage",
        name="Voltage Sensor 2",
        state_topic="power",
        state_class="measurement",
        device_class="voltage",
        unit="V",
        property="ch2Voltage",
        type="float",
    ),
    dict(
        id="ch2_current",
        name="Current Sensor 2",
        state_topic="power",
        state_class="measurement",
        device_class="current",
        unit="mA",
        property="ch2Current",
        type="float",
    ),
    dict(
        id="ch3_voltage",
        name="Voltage Sensor 3",
        state_topic="power",
        state_class="measurement",
        device_class="voltage",
        unit="V",
        property="ch3Voltage",
        type="float",
    ),
    dict(
        id="ch3_current",
        name="Current Sensor 3",
        state_topic="power",
        state_class="measurement",
        device_class="current",
        unit="mA",
        property="ch3Current",
        type="float",
    ),
    dict(
        id="packets_tx",
        name="TX Packets",
        state_topic="localStats",
        state_class="total_increasing",
        device_class=None,
        unit=None,
        property="numPacketsTx",
        type="int",
    ),
    dict(
        id="packets_rx",
        name="RX Packets",
        state_topic="localStats",
        state_class="total_increasing",
        device_class=None,
        unit=None,
        property="numPacketsRx",
        type="int",
    ),
    dict(
        id="packets_rx_bad",
        name="RX Bad Packets",
        state_topic="localStats",
        state_class="total_increasing",
        device_class=None,
        unit=None,
        property="numPacketsRxBad",
        type="int",
    ),
    dict(
        id="online_nodes",
        name="Online Nodes",
        state_topic="localStats",
        state_class="total",
        device_class=None,
        unit=None,
        property="numOnlineNodes",
        type="int",
    ),
    dict(
        id="total_nodes",
        name="Total Nodes",
        state_topic="localStats",
        state_class="total",
        device_class=None,
        unit=None,
        property="numTotalNodes",
        type="int",
    ),
]
