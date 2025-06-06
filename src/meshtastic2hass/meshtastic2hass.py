#!python3

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
import argparse
import asyncio
import json
import os
import signal
import sys
import re

import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
import paho.mqtt.client as mqttClient
import random
from .globals import Globals
from meshtastic import config_pb2, channel_pb2
from pubsub import pub
from tomlkit import toml_file

__author__ = "Michael Wolf aka Mictronics"
__copyright__ = "2025, (C) Michael Wolf"
__license__ = "GPL v3+"
__version__ = "1.0.20"


def onReceiveTelemetry(packet, interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when a telemetry or position packet arrives."""
    # Create JSON from Mesh packet.
    _globals = Globals.getInstance()
    mqtt = _globals.getMQTT()
    sensors = _globals.getSensors()
    topicPrefix = _globals.getTopicPrefix()
    jsonObj = {}
    try:
        fromId = packet.get("fromId")
        shortName = interface.nodes.get(fromId).get("user").get("shortName")
    except AttributeError:
        fromId = packet.get("fromId")
        print(f"Error shortname, id: {interface.nodes.get(fromId)}")
        return
    # Filter nodes
    filterNodes = _globals.getFilterNodes()
    if len(filterNodes) > 0:
        try:
            filterNodes.index(shortName)
        except ValueError:
            return
    # No special characters allowed in Hass config topic
    pattern = _globals.getSpecialChars()
    fromId = re.sub(pattern, '', fromId)
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
    # Calculate hop distance
    hopStart = packet.get("hopStart")
    hopLimit = packet.get("hopLimit")
    if hopStart and hopLimit:
        jsonObj["hopDistance"] = hopStart - hopLimit
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
    try:
        fromId = packet.get("fromId")
        shortName = interface.nodes.get(fromId).get("user").get("shortName")
    except AttributeError:
        fromId = packet.get("fromId")
        print(f"Error shortname, id: {interface.nodes.get(fromId)}")
        return
    # Filter nodes
    filterNodes = _globals.getFilterNodes()
    if len(filterNodes) > 0:
        try:
            filterNodes.index(shortName)
        except ValueError:
            return
    # No special characters allowed in config topic
    pattern = _globals.getSpecialChars()
    fromId = re.sub(pattern, '', fromId)
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
    try:
        _globals = Globals.getInstance()
        mqtt = _globals.getMQTT()
        channelList = _globals.getChannelList()
        topicPrefix = _globals.getTopicPrefix()
        jsonObj = {}
        try:
            fromName = (
                interface.nodes.get(packet.get("fromId")).get("user").get("shortName")
            )
        except AttributeError:
            fromId = packet.get("fromId")
            print(f"Error shortname, id: {interface.nodes.get(fromId)}")
            return
        if packet.get("channel"):
            channelNumber = packet["channel"]
        else:
            channelNumber = 0
        # No special characters allowed in config topic
        pattern = _globals.getSpecialChars()
        channelName = re.sub(pattern, '', channelList[channelNumber])
        # Publish auto discovery configuration for MQTT text entity per channel
        mqttTopic = f"homeassistant/text/{channelName}/config"
        jsonObj["name"] = f"{channelList[channelNumber]}"
        jsonObj["unique_id"] = f"channel_{channelName.lower()}"
        jsonObj["command_topic"] = f"{topicPrefix}/{channelName.lower()}/command"
        jsonObj["state_topic"] = f"{topicPrefix}/{channelName.lower()}/state"
        jsonObj["value_template"] = "{{ value_json.text }}"
        jsonObj["mode"] = "text"
        jsonObj["icon"] = "mdi:message-text"
        mqtt.publish(
            mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
        ).wait_for_publish(1)
        # Publish received text in corresponding channel entity in attributes topic
        jsonObj.clear()
        text = packet.get("decoded").get("text")
        if text:
            jsonObj["text"] = f"{fromName}: {text}"
            mqttTopic = f"{topicPrefix}/{channelName.lower()}/state"
            mqtt.publish(
                mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
            ).wait_for_publish(1)

    except Exception as ex:
        print(f"Error processing text: {ex}")


async def periodic(interval_sec, coro_name, *args, **kwargs):
    """Helper function for running a target periodically."""
    # Loop forever
    while True:
        # Wait an interval
        await asyncio.sleep(interval_sec)
        # Await the target
        await coro_name(*args, **kwargs)


async def publishChannelConfig():
    """Publish known channels in HA to keep them alive when no message are received over long time."""
    try:
        _globals = Globals.getInstance()
        mqtt = _globals.getMQTT()
        channelList = _globals.getChannelList()
        topicPrefix = _globals.getTopicPrefix()
        jsonObj = {}

        for channelName in channelList:
            # No special characters allowed in config topic
            pattern = _globals.getSpecialChars()
            channelName = re.sub(pattern, '', channelName)
            # Publish auto discovery configuration for MQTT text entity per channel
            mqttTopic = f"homeassistant/text/{channelName}/config"
            jsonObj["name"] = f"{channelName}"
            jsonObj["unique_id"] = f"channel_{channelName.lower()}"
            jsonObj["command_topic"] = f"{topicPrefix}/{channelName.lower()}/command"
            jsonObj["state_topic"] = f"{topicPrefix}/{channelName.lower()}/state"
            jsonObj["value_template"] = "{{ value_json.text }}"
            jsonObj["mode"] = "text"
            jsonObj["icon"] = "mdi:message-text"
            mqtt.publish(
                mqttTopic, json.dumps(jsonObj, separators=(",", ":")), qos=1
            ).wait_for_publish(1)

    except Exception as ex:
        print(f"Error processing text: {ex}")


def onReceive(packet, interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when any packet arrives"""
    try:
        if (
            "decoded" in packet
            and packet["decoded"]["portnum"] == "DETECTION_SENSOR_APP"
        ):
            # Forward notification from detection sensor as text message to HA
            onReceiveText(packet, interface)

    except Exception as ex:
        print(f"Error processing text: {ex}")


def onConnect(interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when we connect to a radio"""
    print(f"Connection: {topic.getName()}")


def onDisconnect(interface, topic=pub.AUTO_TOPIC):
    """Callback invoked when we disconnect from a radio"""
    print(f"Lost connection: {topic.getName()}")
    _globals = Globals.getInstance()
    if _globals.getLoop() is not None:
        _globals.getLoop().stop()


def toCamelCase(string):
    """Convert string into camel case"""
    words = string.split("_")
    camelCaseString = "".join(word.capitalize() for word in words)
    return camelCaseString


def onConnected(interface):
    """Callback invoked when we are connected to a radio"""
    try:
        _globals = Globals.getInstance()
        _globals.setMeshtasticInterface(interface)
        print("Radio: connected")
        pub.subscribe(onReceiveText, "meshtastic.receive.text")
        pub.subscribe(onReceiveTelemetry, "meshtastic.receive.telemetry")
        pub.subscribe(onReceivePosition, "meshtastic.receive.position")
        pub.subscribe(onConnect, "meshtastic.connection.established")
        pub.subscribe(onDisconnect, "meshtastic.connection.lost")
        pub.subscribe(onReceive, "meshtastic.receive")

        channelList = _globals.getChannelList()
        node = interface.getNode("^local")
        deviceChannels = node.channels
        for deviceChannel in deviceChannels:
            if deviceChannel.role:
                if deviceChannel.settings.name:
                    channelList.append(deviceChannel.settings.name)

                else:
                    # If channel name is blank, use the modem preset
                    loraConfig = node.localConfig.lora
                    modemPresetEnum = loraConfig.modem_preset
                    modemPresetString = (
                        config_pb2._CONFIG_LORACONFIG_MODEMPRESET.values_by_number[
                            modemPresetEnum
                        ].name
                    )
                    channelList.append(toCamelCase(modemPresetString))

    except Exception as ex:
        print(f"Aborting due to: {ex}")
        interface.close()
        sys.exit(1)


def onMQTTMessage(mqttc, obj, msg):
    """Callback invoke when we receive a message via MQTT"""
    _globals = Globals.getInstance()
    channelList = _globals.getChannelList()
    topicPrefix = _globals.getTopicPrefix()
    interface = _globals.getMeshtasticInterface()
    # Check for correct topic
    if msg.topic.startswith(topicPrefix):
        channel = msg.topic.split("/")[-1]
        try:
            # Check for existing channel
            channel_index = channelList.index(channel)
        except ValueError:
            return
        # Check for enabled channel
        ch = interface.localNode.getChannelByChannelIndex(channel_index)
        if (ch and ch.role != channel_pb2.Channel.Role.DISABLED):
            # Forward message to channel
            # print(channel + " " + " " + msg.payload.decode('utf-8'))
            interface.sendText(
                     msg.payload.decode('utf-8'),
                     "^all",  # Broadcast
                     wantAck=False,
                     wantResponse=False,
                     channelIndex=channel_index,
                     onResponse=None,
                 )


def onMQTTConnect(client, userdata, flags, reason_code, properties):
    """Callback invoke when we connect to MQTT broker"""
    if reason_code != 0:
        print(f"MQTT: unexpected connection error {reason_code}")
        _globals = Globals.getInstance()
        if _globals.getLoop() is not None:
            _globals.getLoop().stop()


def onMQTTDisconnect(client, userdata, flags, reason_code, properties):
    """Callback invoke when we disconnect from MQTT broker"""
    if reason_code != 0:
        print(f"MQTT: unexpected disconnection error {reason_code}")
        _globals = Globals.getInstance()
        if _globals.getLoop() is not None:
            _globals.getLoop().stop()


def onMQTTPublish(client, userdata, mid, reason_codes, properties):
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

    parser.add_argument(
        "--use-network",
        help="Use network connection to Meshtastic interface instead of serial",
        default=False,
        required=False,
    )

    parser.add_argument(
        "--hostname",
        help="Meshtastic interface network hostname or IP",
        default=None,
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
    client_id = f'meshtastic2hass-{random.randint(0, 100)}'
    try:
        mqtt = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION2, client_id, True)
        _globals.setMQTT(mqtt)
        _globals.setTopicPrefix(args.mqtt_topic_prefix)
        mqtt.on_message = onMQTTMessage
        mqtt.on_connect = onMQTTConnect
        mqtt.on_disconnect = onMQTTDisconnect
        mqtt.on_publish = onMQTTPublish
        mqtt.username_pw_set(args.mqtt_user, args.mqtt_password)
        mqtt.connect(args.mqtt_host, int(args.mqtt_port))
        mqtt.subscribe([(f"{args.mqtt_topic_prefix}/+", 0)])
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
            args.use_network = cfg.get("use_network")
            args.hostname = cfg.get("hostname")
            _globals.setFilterNodes(cfg.get("meshtastic").get("filter_nodes"))
        else:
            print(f"Error: configuration file {args.config} not found!")
            sys.exit(1)

    initMQTT()
    try:
        if args.use_network and isinstance(args.hostname, str):
            client = meshtastic.tcp_interface.TCPInterface(args.hostname , noProto=False)
        else:
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
    except FileNotFoundError as e:
        print("Serial interface not found.")
        print(f"Error was: {e}")
        sys.exit(1)
    except OSError as e:
        print("Network interface not found.")
        print(f"Error was: {e}")
        sys.exit(1)

    # We assume client is fully connected now
    onConnected(client)
    # Wait for packets
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _globals.setLoop(loop)
    # Publish channel configuration every hour via MQTT to avoid unavailability in HA
    loop.create_task(periodic(3600, publishChannelConfig))
    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
