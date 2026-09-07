# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python daemon that bridges a Meshtastic mesh radio (via USB serial or TCP) to Home Assistant via MQTT. It listens for Meshtastic telemetry/position/text packets, publishes MQTT Discovery configs + state so Home Assistant auto-creates entities, and forwards MQTT messages back into Meshtastic channels as text.

## Commands

Install deps:
```bash
pip install .
```

Run (either CLI flags or a TOML config file; running with no args prints help and exits):
```bash
python src/meshtastic2hass/meshtastic2hass.py --config path/to/config.toml
# or, once installed as a package, the console script:
meshtastic2hass --config path/to/config.toml
```

Build the package (PyScaffold/setuptools-scm project, versioned from git tags):
```bash
tox -e clean   # remove build/dist/*.egg-info
tox -e build   # build sdist + wheel via PEP517
```

Lint config lives in `setup.cfg` (`[flake8]`, max-line-length 88) and `.trunk/trunk.yaml` (flake8, black, isort, ruff, bandit, markdownlint, etc. — run via the `trunk` CLI if installed).

There is no test suite in this repo currently (`.coveragerc` exists but no `tests/` directory).

## Architecture

The whole app is ~950 lines across two files in `src/meshtastic2hass/`:

- **`app_globals.py`** — plain module holding all shared state as top-level attributes (a module is already a process-wide singleton, so there's no class/instance here): parsed CLI `args`, the `mqtt` client, the connected Meshtastic `interface`, the asyncio `loop`, the node `filterNodes` list, the discovered `channelList`, and — importantly — `sensors`, a declarative list of dicts describing every Home Assistant sensor entity this bridge can create (id, display name, which telemetry sub-object it reads from, HA `device_class`/`unit`/`state_class`, and value type). Callers do `import app_globals as g` and read/write `g.<attr>` directly. Adding a new exposed telemetry field means adding one dict to `g.sensors`, not touching the callback logic. Named `app_globals`, not `globals`, because `globals` is also the name of a third-party dependency in `setup.cfg` (`globals>=0.3.36`) — a bare `import globals` resolves to that package once installed as a real package (not run as a loose script), not this module.
- **`meshtastic2hass.py`** — entry point and all runtime logic. Flow:
  1. `main()` parses args/TOML config into the `app_globals` module, opens a `SerialInterface` or `TCPInterface` from the `meshtastic` package, and connects to the MQTT broker (`initMQTT`).
  2. `onConnected()` subscribes Meshtastic's `pubsub` events (`meshtastic.receive.text`, `.telemetry`, `.position`, connection established/lost) and discovers the radio's configured channels (`g.channelList`), used later to route MQTT text back to the right Meshtastic channel.
  3. `onReceiveTelemetry`/`onReceivePosition`/`onReceiveText` each: look up the sending node's short name, apply `g.filterNodes` (if set, silently drop unlisted nodes), strip HA-illegal characters from the topic (`g.specialChars` regex), publish an MQTT Discovery `config` topic (built generically from `g.sensors` for telemetry) plus the actual state/attributes payload.
  4. `onMQTTMessage` is the reverse path: an MQTT publish under `<topic_prefix>/<channel>` gets matched against the discovered channel list and forwarded into the mesh via `interface.sendText(...)`, provided the channel isn't disabled.
  5. `publishChannelConfigHourly` (an asyncio task started in `main()`) sleeps 3600s in a loop and calls `publishChannelConfig()` each time, republishing channel discovery configs so HA doesn't mark the text entities unavailable during long quiet periods.
- Everything is single-process, single-threaded except for the MQTT client's own network loop (`mqtt.loop_start()`) and the asyncio event loop driving the hourly task; there's no concurrency to reason about beyond that.
- Config precedence: TOML config (`--config`) is read *after* CLI arg parsing and overwrites the parsed args/topic prefix/filter nodes — so config file wins over other CLI flags when both are given.

See `README.md` for the CLI flags and `filter_nodes` config semantics, `Automation.md` for example Home Assistant automations that publish MQTT back into a Meshtastic channel, and `Helper.md` for an HA template-sensor example (uptime formatting).
