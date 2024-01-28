#!python3

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
import argparse
import asyncio
import json
import os
import signal
import sys

import meshtastic
import meshtastic.serial_interface
import paho.mqtt.client as mqttClient
from globals import Globals
from pubsub import pub
from tomlkit import toml_file

__author__ = "Michael Wolf aka Mictronics"
__copyright__ = "2024, (C) Michael Wolf"
__license__ = "GPL v3+"
__version__ = "1.0.4"


def onReceiveTelemetry(packet, interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when a telemetry or position packet arrives."""
    # Create JSON from Mesh packet.
    _globals = Globals.getInstance()
    mqtt = _globals.getMQTT()
    sensors = _globals.getSensors()
    topicPrefix = _globals.getTopicPrefix()
    jsonObj = {}
    fromId = packet.get("fromId")
    shortName = interface.nodes.get(fromId).get("user").get("shortName")
    # No special characters allowed in Hass config topic
    fromId = fromId.strip("!")
    # Publish auto discovery configuration for sensors
    for sensor in sensors:
        jsonObj.clear()
        mqttTopic = f"homeassistant/sensor/{fromId}/{sensor['id']}/config"
        jsonObj["name"] = f"{shortName} {sensor['name']}"
        jsonObj["unique_id"] = f"{shortName.lower()}_{sensor['id']}"
        jsonObj["state_topic"] = f"{topicPrefix}/{fromId}/{sensor['state_topic']}"
        jsonObj["state_class"] = "measurement"
        jsonObj["platform"] = "mqtt"
        if sensor["device_class"]:
            jsonObj["device_class"] = sensor["device_class"]
        if sensor["unit"]:
            jsonObj["unit_of_measurement"] = sensor["unit"]
        if sensor["type"] == "float":
            jsonObj["value_template"] = (
                "{{ " + f"(value_json.{sensor['property']} | float) | round(1)" + " }}"
            )
        elif sensor["type"] == "int":
            jsonObj["value_template"] = (
                "{{ " + f"(value_json.{sensor['property']} | int)" + " }}"
            )

        mqtt.publish(
            mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
        ).wait_for_publish(1)
    # Publish telemetry as sensor topics
    jsonObj.clear()
    rssi = packet.get("rxRssi")
    if rssi:
        jsonObj["rssi"] = rssi
    else:
        jsonObj["rssi"] = 0
    snr = packet.get("rxSnr")
    if snr:
        jsonObj["snr"] = snr
    else:
        jsonObj["snr"] = 0
    # Each telemetry type has its own topic
    telemetry = packet.get("decoded").get("telemetry")
    if telemetry:
        devMetrics = telemetry.get("deviceMetrics")
        envMetrics = telemetry.get("environmentMetrics")
        powerMetrics = telemetry.get("powerMetrics")
        if devMetrics:
            mqttTopic = f"{topicPrefix}/{fromId}/device"
            jsonObj = jsonObj | devMetrics
        elif envMetrics:
            mqttTopic = f"{topicPrefix}/{fromId}/environment"
            jsonObj = jsonObj | envMetrics
        elif powerMetrics:
            mqttTopic = f"{topicPrefix}/{fromId}/power"
            jsonObj = jsonObj | powerMetrics

        mqtt.publish(
            mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
        ).wait_for_publish(1)


def onReceivePosition(packet, interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when a position packet arrives."""
    _globals = Globals.getInstance()
    mqtt = _globals.getMQTT()
    topicPrefix = _globals.getTopicPrefix()
    jsonObj = {}
    fromId = packet.get("fromId")
    shortName = interface.nodes.get(fromId).get("user").get("shortName")
    # No special characters allowed in config topic
    fromId = fromId.strip("!")
    # Publish auto discovery configuration for device tracker
    mqttTopic = f"homeassistant/device_tracker/{fromId}/config"
    jsonObj["name"] = f"{shortName} Position"
    jsonObj["unique_id"] = f"{shortName.lower()}_position"
    jsonObj["json_attributes_topic"] = f"{topicPrefix}/{fromId}/attributes"
    jsonObj["source_type"] = "gps"
    mqtt.publish(
        mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
    ).wait_for_publish(1)
    # Publish position payload for device tracker in attributes topic
    jsonObj.clear()
    position = packet.get("decoded").get("position")
    if position:
        jsonObj["longitude"] = position.get("longitude")
        jsonObj["latitude"] = position.get("latitude")
        jsonObj["satsInView"] = position.get("satsInView")
        jsonObj["location_accuracy"] = 1
        mqttTopic = f"{topicPrefix}/{fromId}/attributes"
        mqtt.publish(
            mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
        ).wait_for_publish(1)


def onReceiveText(packet, interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when a text packet arrives."""
    _globals = Globals.getInstance()
    mqtt = _globals.getMQTT()
    topicPrefix = _globals.getTopicPrefix()
    jsonObj = {}
    fromId = packet.get("fromId")
    shortName = interface.nodes.get(fromId).get("user").get("shortName")
    # No special characters allowed in config topic
    fromId = fromId.strip("!")
    # Publish auto discovery configuration for MQTT text entity
    mqttTopic = f"homeassistant/text/{fromId}/config"
    jsonObj["name"] = f"{shortName} Text"
    jsonObj["unique_id"] = f"{shortName.lower()}_text"
    jsonObj["command_topic"] = f"{topicPrefix}/{fromId}/command"
    jsonObj["state_topic"] = f"{topicPrefix}/{fromId}/state"
    jsonObj["value_template"] = "{{ value_json.text }}"
    jsonObj["mode"] = "text"
    jsonObj["icon"] = "mdi:message-text"
    mqtt.publish(
        mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
    ).wait_for_publish(1)
    # Publish position payload for device tracker in attributes topic
    jsonObj.clear()
    text = packet.get("decoded").get("text")
    if text:
        jsonObj["text"] = text
        mqttTopic = f"{topicPrefix}/{fromId}/state"
        mqtt.publish(
            mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
        ).wait_for_publish(1)


def onConnect(interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when we connect to a radio"""
    print(f"Connection: {topic.getName()}")


def onDisconnect(interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when we disconnect from a radio"""
    print(f"Connection: {topic.getName()}")
    _globals = Globals.getInstance()
    _globals.getLoop().stop()


def onConnected(interface):
    """Callback invoked when we are connected to a radio"""
    try:
        _globals = Globals.getInstance()
        print("Radio: connected")
        pub.subscribe(onReceiveText, "meshtastic.receive.text")
        pub.subscribe(onReceiveTelemetry, "meshtastic.receive.telemetry")
        pub.subscribe(onReceivePosition, "meshtastic.receive.position")
        pub.subscribe(onConnect, "meshtastic.connection.established")
        pub.subscribe(onDisconnect, "meshtastic.connection.lost")

    except Exception as ex:
        print(f"Aborting due to: {ex}")
        interface.close()
        sys.exit(1)


def onMQTTMessage(mqttc, obj, msg):
    """Callback invoke when we receive a message via MQTT"""
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def onMQTTConnect(client, userdata, flags, rc):
    """Callback invoke when we connect to MQTT broker"""
    if rc != 0:
        print(f"MQTT: unexpected connection error {rc}")
        _globals = Globals.getInstance()
        _globals.getLoop().stop()


def onMQTTDisconnect(client, userdata, rc):
    """Callback invoke when we disconnect from MQTT broker"""
    if rc != 0:
        print(f"MQTT: unexpected disconnection error {rc}")
        _globals = Globals.getInstance()
        _globals.getLoop().stop()


def onMQTTPublish(client, userdata, mid):
    """Callback invoked when a message has completed transmission to the broker"""
    pass


def initArgParser():
    """Initialize the command line argument parsing."""
    _globals = Globals.getInstance()
    parser = _globals.getParser()
    args = _globals.getArgs()

    parser.add_argument(
        "--config",
        help="Path to configuration file in TOML format.",
        default=None,
        required=False,
    )

    parser.add_argument(
        "--dev",
        help="The device the Meshtastic device is connected to, i.e. /dev/ttyUSB0",
        default=None,
        required=False,
    )

    parser.add_argument(
        "--mqtt-host",
        help="The MQTT broker host name or IP.",
        default="localhost",
        required=False,
    )

    parser.add_argument(
        "--mqtt-port", help="The MQTT broker port.", default=1883, required=False
    )

    parser.add_argument(
        "--mqtt-user", help="The MQTT broker user name.", default=None, required=False
    )

    parser.add_argument(
        "--mqtt-password",
        help="The MQTT broker password.",
        default=None,
        required=False,
    )

    parser.add_argument(
        "--mqtt-topic-prefix",
        help="The MQTT topic prefix",
        default="msh/2/json",
        required=False,
    )

    parser.set_defaults(deprecated=None)
    parser.add_argument("--version", action="version", version=f"{__version__}")

    args = parser.parse_args()
    _globals.setArgs(args)
    _globals.setParser(parser)


def initMQTT():
    """Initialize the MQTT client and connect to broker"""
    _globals = Globals.getInstance()
    args = _globals.getArgs()
    mqtt = _globals.getMQTT()
    try:
        mqtt = mqttClient.Client()
        _globals.setMQTT(mqtt)
        _globals.setTopicPrefix(args.mqtt_topic_prefix)
        mqtt.on_message = onMQTTMessage
        mqtt.on_connect = onMQTTConnect
        mqtt.on_disconnect = onMQTTDisconnect
        mqtt.on_publish = onMQTTPublish
        mqtt.username_pw_set(args.mqtt_user, args.mqtt_password)
        mqtt.connect(args.mqtt_host, int(args.mqtt_port))
        mqtt.loop_start()
    except Exception as e:
        print(f"MQTT client error: {e}")
        sys.exit(1)


def main():
    """Main program function"""

    def signal_handler(signal, frame):
        client.close()
        mqtt.disconnect()
        mqtt.loop_stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    _globals = Globals.getInstance()
    parser = argparse.ArgumentParser(
        prog="meshtastic2hass",
        description="Connects Meshtastic radios via MQTT to Home Assistant (Hass).",
        epilog="License GPL-3+ (C) 2024 Michael Wolf, www.mictronics.de",
    )
    _globals.setParser(parser)
    initArgParser()
    args = _globals.getArgs()
    mqtt = _globals.getMQTT()
    cfg = None

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    elif args.config is not None:
        if os.path.exists:
            cfg = toml_file.TOMLFile(args.config).read()
            args.dev = cfg.get("device")
            _globals.setTopicPrefix(cfg.get("mqtt").get("topic_prefix"))
            args.mqtt_user = cfg.get("mqtt").get("user")
            args.mqtt_password = cfg.get("mqtt").get("password")
            args.mqtt_host = cfg.get("mqtt").get("host")
            args.mqtt_port = cfg.get("mqtt").get("port")
        else:
            print(f"Error: configuration file {args.config} not found!")
            sys.exit(1)

    initMQTT()
    try:
        client = meshtastic.serial_interface.SerialInterface(
            devPath=args.dev, noProto=False
        )
    except PermissionError as ex:
        username = os.getlogin()
        message = "Permission Error:\n"
        message += "  Need to add yourself to the 'dialout' group by running:\n"
        message += f"     sudo usermod -a -G dialout {username}\n"
        message += "  After running that command, log out and re-login for it to take effect.\n"
        message += f"Error was:{ex}"
        print(message)
        sys.exit(1)

    # We assume client is fully connected now
    onConnected(client)
    # Wait for packets
    loop = asyncio.get_event_loop()
    _globals.setLoop(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
