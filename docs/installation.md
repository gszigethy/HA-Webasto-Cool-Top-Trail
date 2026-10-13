# Installation and operation

## Prepare ESPHome

Copy `esp32/bridge.example.yaml` and `esp32/webasto_ir.h` into the same ESPHome
configuration directory. ESPHome's `includes` copies the header into the build.
Use ESPHome 2026.9.1 or newer. Choose the actual board and GPIOs before flashing.
The debugging ESP is ESP32-PICO-D4 with 4 MB flash, RX32/TX26. The existing
caravan prototype has TX2; RX23 was only a commented example, not verified wiring.

Set local `secrets.yaml` using the keys in `esp32/secrets.example.yaml`. Generate
a private native-API encryption key; the committed example key is for validation
only. Set device/friendly names, board, receiver and transmitter pin substitutions.
Keep existing unrelated caravan functionality when merging the transport.
Remove the old AC select, slider, buttons and fixed-pulse automations so they do
not compete with the full-state climate controller. Preserve them in your own
backup if you need rollback. This repository has not modified that deployed ESP.

```bash
esphome config bridge.example.yaml
esphome compile bridge.example.yaml
# When you choose to deploy:
esphome upload bridge.example.yaml
```

The bridge enables Wi-Fi, encrypted native API and ESPHome OTA. No new HA YAML
helpers, MQTT broker, HTTP endpoint, or custom ESPHome climate component is needed.
Pair the device with built-in ESPHome. Its API action is
`esphome.webasto_ir_bridge_send_frame` with a `frame` string parameter. ESPHome
converts hyphens in the node name to underscores for the action name. Received
and transmitted frame text sensors appear as HA sensor entities.

The action validates header/length/checksums, transmits at nominal 38 kHz, waits
300 ms for the nonblocking RMT completion, checks transmitter status, and returns
native API success/error. HA waits for this response. It confirms local handling,
not IR reception by the air conditioner. Use the documented bridge action rather
than substituting an unrelated service with a similar name.

The receiver assembles both halves using a 30 ms idle interval, a 64 KB buffer,
and 50 μs filter. Its standalone codec rejects incomplete/extra-edge frames,
wrong framing, ambiguous bits and checksum failures. No raw noise is published
to HA; only valid 16-byte frames are published. A receiver can hear its own
transmitter, which is still an observed command rather than appliance feedback.

## Transmitter-only installation

If there is no receiver on the caravan ESP, remove the `remote_receiver` section;
keep both text sensors and the send action. The Received IR frame entity remains
unknown while the API is connected and becomes unavailable on disconnect. Select
it as the connection marker, and enable **default starting settings** in the
custom integration UI. Use default settings only when you accept initializing
requested state without learning the physical remote: power off, cool mode,
24 °C, auto fan, display on, panel unlocked, Sleep off, timers disabled, stored
ON/OFF times 09:00/10:00, unknown bits zero. Opting in does not send a command.
The first explicit control applies that complete profile to the appliance.

A receiver on a separate ESP can also supply frames. The sender and receiver
must serve the same AC. Availability requires the selected receiver sensor to
exist and not be unavailable, and the selected sender action to be registered;
native-API failures at send time are also reported. A separate receiver does
not provide transmitter-device availability telemetry on its own.

Without a receiver, physical remote changes and automatic timer events cannot
be tracked. Future HA commands use the last commanded profile and may overwrite
changes made elsewhere. The integration saves the last frame across reloads.

## Install HACS integration

Add this repository as type Integration in HACS, install, restart HA, and add
Webasto Cool Top Trail via Devices & services. Select the correct Received IR
frame sensor and send_frame action. Choose an optional existing temperature
sensor with °C or °F measurements. There is no room sensor in the IR protocol.

For manual installation, copy `custom_components/webasto_cool_top_trail` into
`config/custom_components`, restart, then use the same UI flow. Do not configure
this custom integration in `configuration.yaml`.

Each receiver entity can be assigned once; multiple AC bridges have independent
entries, devices, saved frames and commands. Reconfigure from the entry menu to
change bindings, name, default-profile option or room sensor. Omit the optional
room sensor to remove it. Existing version 0.0.1 scaffold entries keep their
entry/entity identity but require **Reconfigure** to select transport bindings.
No climate control is silently attached during migration.

## Operation and recovery

With a receiver and no saved/default frame, controls stay unavailable until a
valid physical-remote command arrives. Set the remote to Celsius before learning
if you intend to adjust temperature. Ready means transport plus a valid template;
it does not mean the AC has acknowledged it. A disconnected bridge makes control
entities unavailable, retains its template and sends nothing on reconnect.

The primary climate entity uses HA standard services. Changing temperature while
off leaves power off. Turn on resumes the packet's stored operating mode. A
combined set_temperature request with hvac_mode is one full-state transmission.
HA unit conversion happens before rounding to the AC's nearest whole Celsius
setpoint; out-of-range values are rejected. Target temperature is absent in fan
mode. No speculative compressor `hvac_action` is reported.

On/off schedules belong to the appliance, using local wall-clock HH:MM without
seconds. Every explicit send synchronizes its clock with HA; the Synchronize
clock button makes that an explicit action. There is no background clock sync
or automatic HA schedule evaluation. Timers retain their times while disabled.
The receiver cannot observe the appliance starting itself when a timer fires,
and HA does not predict a state transition. Daylight-saving or timezone changes
require a subsequent command/clock sync; schedules have no timezone/DST field.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No send action in selector | Pair ESPHome; confirm bridge firmware has `api.actions.send_frame`; check its connection |
| Awaiting remote frame | Point a Celsius remote at the receiver; check pin/inversion and receiver position |
| Disconnected | Check Wi-Fi, API pairing/encryption, selected sensor/action and entity availability |
| Temperature requires Celsius | Switch the physical remote to °C and send a normal command; other controls preserve Fahrenheit frames |
| Unknown room temperature | Configure an actual room sensor; confirm numeric °C/°F state and connectivity |
| Some presses missing | Capture firmware raw logs; bad timing/extra edges are rejected; avoid changing tolerances to accept noise |
| HA settings change but AC does not | Check TX GPIO, emitter drive/carrier/position, supply, and AC response; local API success is not optical proof |
| Timer appears active at normal clock | ON/OFF icons remain after editing timeout; clock display alone does not mean disabled |

Protocol status diagnostics expose the template, source (`unknown`, `default`,
`received`, `commanded`, `restored`), and session receive/command timestamps.
These timestamps are HA observation times; bytes 2/3/14 are the remote/device
clock and can be several minutes different. Avoid sharing device/network secrets
when reporting logs. See the physical acceptance checklist before relying on
unattended appliance control.
