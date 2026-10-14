# HA Webasto Cool Top Trail

[![CI](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/ci.yml/badge.svg)](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/ci.yml)
[![Validate](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/validate.yml/badge.svg)](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Home Assistant controls for **Houghton-made Webasto Cool Top Trail** caravan and
motorhome air conditioners, installed through **HACS** and using **ESPHome** IR
hardware. One climate entity provides power, temperature, HVAC modes, fan speed,
and Sleep. Auxiliary entities provide panel display, panel touch-control lock,
and ON/OFF schedules.

**Version 0.1.0 is a development implementation.** Remote frames, protocol
fields, HA service behavior, and the firmware build are verified. Synthesized
commands have **not yet been tested against the physical air conditioner**.
IR state is assumed: receiving or sending a command cannot prove AC operation.
No compressor activity, room-temperature telemetry, or fault feedback is invented.

## Does this require a physical remote?

No. This integration implements a fixed CARRIER_AC128 protocol and generates
complete state packets; it does not learn separate button waveforms. There is
no IR pairing with the appliance. For the supported Webasto Cool Top Trail
profile, a transmitter-only installation can use the optional default state
without owning or capturing a remote. Enable **Use default state** during setup;
no command is sent until you operate a control. The default uses Celsius.

Receiving a physical remote frame is optional. It supplies a full-state template
so commands preserve its display unit, timer values and unknown flags, and lets
HA follow subsequent physical remote commands. Without a received frame or an
explicitly enabled default state, controls wait for initialization. This is a
software initialization policy, not an appliance pairing requirement.

A receiver detects remote commands, not feedback from the air conditioner.
Protocol support is verified from this remote's recordings; generated commands
still need appliance acceptance testing. Sharing the CARRIER_AC128 wire format
alone does not establish compatibility with every Houghton or Carrier model.

## Setup

Requires Home Assistant **2026.10.1+**, ESPHome **2026.9.1+**, and an ESP32 with
an IR transmitter. An IR receiver is recommended for physical-remote tracking;
transmitter-only use is supported with an explicit default starting profile.

1. Prepare the [ESPHome bridge](esp32/bridge.example.yaml) and its companion
   [header](esp32/webasto_ir.h), using your board, actual pins, Wi-Fi credentials,
   and native API encryption key. Build/flash it yourself when ready. The example
   uses GPIO32 RX and GPIO26 TX on the debugging ESP; the existing caravan
   prototype uses **GPIO2 TX**. See [installation](docs/installation.md).
2. Pair the bridge through Home Assistant's built-in **ESPHome** integration.
3. In HACS → Custom repositories, add
   `https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail`, type **Integration**.
   Download and restart Home Assistant. This is a custom repository, not a HACS
   default-catalog entry; use `main` while no releases are published.
4. Add **Webasto Cool Top Trail** under Settings → Devices & services.
   Select the bridge's **Received IR frame** sensor and
   `esphome.<device_name>_send_frame` action. Optionally select a room-temperature
   sensor. For transmitter-only use, explicitly enable default starting settings.
5. With a receiver, press a normal button on the physical remote while pointing
   it at the receiver. A valid frame initializes all settings; climate controls
   become available. No command is sent by installation, startup, or reload.

Controls change the complete 16-byte state and preserve untouched auxiliary
settings, unknown bits, and the last observed counter. Every explicit send
synchronizes the clock to Home Assistant local time and calculates both checksums.

## Entities

| Entity | Controls / information |
| --- | --- |
| Climate | `off`, `cool`, `heat`, `dry`, `fan_only`, `heat_cool`; 16–30 °C or 60–86 °F, native 1-degree steps; supported fan speeds; `none` / `sleep` presets |
| Panel display switch | Air-distribution-panel display on/off |
| Panel control lock switch | Panel touch controls locked/unlocked |
| On timer / Off timer switches | Independent schedule enables; both can be enabled |
| On time / Off time | Stored local HH:MM schedule times, retained while disabled |
| Synchronize clock button | Send current settings with HA local clock |
| Protocol status sensor | Bridge connectivity/readiness and assumed-state diagnostics |

The remote's AUTO mode maps to HA `heat_cool` with **one setpoint**. Auto fan
is distinct and supported in heat/cool. Dry uses low fan; fan-only has no target
temperature. Sleep is enabled only during heat/cool. Louvers are manual: no
swing entity. No ECO control or C/F display selector is exposed without enough
local evidence. Celsius and Fahrenheit remote profiles both support target edits.
HA displays its preferred units while commands retain the learned remote profile.
See the [Fahrenheit captures and conversion rules](captures/live/2026-10-14-fahrenheit/README.md).

## Documentation

- [Installation and troubleshooting](docs/installation.md)
- [Entity reference and examples](docs/entity-map.md)
- [Functional design (FD)](docs/functional-design.md)
- [Technical design (TD)](docs/technical-design.md)
- [IR protocol: framing, byte map, checksums and evidence](docs/ir-protocol.md)
- [Validation and appliance acceptance checklist](docs/validation.md)
- [MVP captures](captures/live/2026-10-13-mvp/README.md)
- [Auxiliary captures](captures/live/2026-10-13-auxiliary/README.md)
- [Baseline review](esp32/baseline-review.md) and [decoded packets](docs/baseline-decoded.md)
- [Capture procedure](docs/ir-capture.md) and [ESPHome notes](esp32/README.md)
- [Hungarian manufacturer manual](https://varadicaravan.hu/wp-content/uploads/2022/04/Webasto-Cool-Top-Trail-20_24.pdf)

The supplied manual covers Cool Top Trail 20/24 (Belaire H2000/H2400). Exact
appliance/remote variants still need physical acceptance testing before support
for further Houghton/Webasto models can be claimed.

## Development

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest --cov=custom_components.webasto_cool_top_trail
```

Use `python -m pytest` so the repository is on the module search path. The test
plugin pins HA and pytest dependencies. `g++` is required to replay captures
against the deployed C++ wire codec. Tests use an isolated HA instance, fake
ESPHome native services, and archived frames; they never contact a live HA or ESP.
CI runs these checks plus ESPHome example validation/build, hassfest, and HACS
validation. Only the HACS Brands check is skipped pending registration.

Keep local secrets and device backups out of Git. No firmware or HA configuration
is deployed by this repository's tests or workflows. See [contributing](CONTRIBUTING.md).
