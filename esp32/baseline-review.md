# Baseline review

The user supplied the working caravan ESPHome YAML on 2026-10-13. The archived
[baseline.yaml](baseline.yaml) preserves the control logic and every signed IR
duration. The API key is replaced with `!secret api_encryption_key`; node/network
names, address, and domain use placeholders. Private original data is not
included in this repository.

## Implemented behavior

| Item | Baseline |
| --- | --- |
| ESP32 | `esp32dev`, ESP-IDF framework |
| IR transmitter | GPIO2, ID `transmitter_ir`, configured carrier 38 kHz, duty 50% |
| RF transmitter | GPIO22, ID `transmitter_rf`; no RF commands in this YAML |
| AC mode | Optimistic select, `Off`, `Heating`, `Cooling` |
| Setpoint | Optimistic number, 16-30 °C, step 1 °C, initial value 22 |
| OFF button | Replays the same packet as selecting `Off` |
| Receiver | Commented-out GPIO23 example; no active receiver or raw dumping |
| Logging | WARN |

Selecting a mode first updates `ac_mode_global`, waits one second, then sends
OFF or re-applies the current slider value. The slider sends one of 30 stored
heat/cool packets when the global mode is non-off. Changing temperature while
off only changes the optimistic setpoint.

There are 32 transmit actions but 31 distinct signed-duration arrays: the OFF
packet appears twice. See [the extracted corpus](../captures/baseline/packets.json)
and [protocol analysis](../docs/ir-protocol.md).

## Issues to address in the replacement

- The separate OFF button sends IR without updating the select/global state.
  A later slider movement can send a heat/cool packet while the physical AC is
  off. This conclusion follows from the YAML, not a reproduced hardware test.
- Initial mode `Off` and setpoint 22 are software defaults, not appliance feedback.
- The stored packets contain old clock fields and fixed auxiliary settings.
  Replaying a temperature packet also replays those settings.
- Non-blocking transmission and delayed mode actions need serialization/coalescing
  when a user changes several settings quickly.
- Fan modes, sleep, display, lock, timers, dry, and auto HVAC are not independently
  controlled here. Native climate commands should construct complete packets.
- The minimum ESPHome version declared in the original is not proof that every
  option works on that version. This archive is config-validated on ESPHome
  2026.9.1; it is not compiled, flashed, or tested on the live device by CI.

## Local validation

Copy `secrets.example.yaml` to the ignored `secrets.yaml` only for validation,
then run `esphome config esp32/baseline.yaml` from the repository root. The example
key/passwords are publicly known test placeholders. Configure your own secrets,
node identity, and network settings before deployment.

The archive deliberately retains the original control behavior. Improvements
belong in a separate implementation so protocol regression comparisons remain
traceable.
