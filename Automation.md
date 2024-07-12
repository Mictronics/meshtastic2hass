# Automation setup in Home Assistant

This is an example automation how to forward a state from Home Assistant via MQTT to a Meshtastic channel.

Add a new automation via YAML editor in Home Assistant:
```yaml
alias: LongFast Publish
description: Publish message via MQTT to LongFast channel
trigger:
  - platform: state
    entity_id:
      - text.longfast
condition: []
action:
  - service: mqtt.publish
    metadata: {}
    data:
      qos: "0"
      retain: false
      topic: msh/2/json/{{states.text.longfast.name}}
      payload_template: "{{states.text.longfast.state}}"
mode: single
```
The example takes the state (text input) from the LongFast channel text entity and echos back to the LongFast channel in Meshtastic.

This automation setup will send the state of a binary switch in HA to the Meshtastic Private channel:
```yaml
alias: Private Publish
description: Publish message via MQTT to Private channel
trigger:
  - platform: state
    entity_id:
      - switch.openevse_charger_switch_0
condition: []
action:
  - service: mqtt.publish
    metadata: {}
    data:
      qos: "0"
      retain: false
      topic: msh/2/json/Private
      payload_template: "Charger: {{states.switch.openevse_charger_switch_0.state}}"
mode: single
```

The topic prefix must match the configuration in meshtastic2hass.