# Meshtastic to Home Assistant (Hass)

A Python client for use with Meshtastic devices. The client connects to a mesh radio via USB serial port. Telemetry and position messages from the mesh are published to an MQTT broker and further into Home Assistant. All MQTT entities will by auto discovered in Home Assistant.

## Usage

```bash
usage: meshtastic2hass [-h] --dev DEV --mqtt-host MQTT_HOST [--mqtt-port MQTT_PORT] --mqtt-user MQTT_USER --mqtt-password
                       MQTT_PASSWORD [--mqtt-topic-prefix MQTT_TOPIC_PREFIX] [--version]

Connects Meshtastic radios via MQTT to Home Assistant (Hass).

options:
  -h, --help            show this help message and exit
  --config CONFIG       Path to configuration file in TOML format.
  --dev DEV             The device the Meshtastic device is connected to, i.e. /dev/ttyUSB0
  --mqtt-host MQTT_HOST
                        The MQTT broker host name or IP.
  --mqtt-port MQTT_PORT
                        The MQTT broker port.
  --mqtt-user MQTT_USER
                        The MQTT broker user name.
  --mqtt-password MQTT_PASSWORD
                        The MQTT broker password.
  --mqtt-topic-prefix MQTT_TOPIC_PREFIX
                        The MQTT topic prefix.
  --version             show program's version number and exit
```
