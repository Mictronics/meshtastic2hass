# Meshtastic to Home Assistant (Hass)

A Python client for use with Meshtastic devices. The client connects to a mesh radio via USB serial port. Telemetry and position messages from the mesh are published to an MQTT broker and further into Home Assistant. All MQTT entities will by auto discovered in Home Assistant.

## Usage

```bash
usage: meshtastic2hass [-h] [--config CONFIG] [--dev DEV] [--mqtt-host MQTT_HOST] [--mqtt-port MQTT_PORT] [--mqtt-user MQTT_USER]
                       [--mqtt-password MQTT_PASSWORD] [--mqtt-topic-prefix MQTT_TOPIC_PREFIX] [--use-network USE_NETWORK]
                       [--hostname HOSTNAME] [--version]

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
                        The MQTT topic prefix
  --use-network USE_NETWORK
                        Use network connection to Meshtastic interface instead of serial
  --hostname HOSTNAME   Meshtastic interface network hostname or IP
  --version             show programs version number and exit
```
## Node Filter

By default all received Meshtastic nodes will create entities in Home Assistant.

This might be an undesired behavior when only some nodes are of interest. A node filter can be defined in config.toml.

`filter_nodes = []` takes a set of Meshtastic nodes short names to be includes in filter. Only these nodes will be forwarded to home assistant via MQTT topic, hence creating entities. Keep empty to forward all nodes.

Receiving channels text from nodes is not filtered at all.

## Install packages with pip and requirements.txt

The following command installs packages in bulk according to the configuration file, requirements.txt. In some environments, use pip3 instead of pip.

`pip install -r requirements.txt`