# Validation and acceptance

## Evidence already obtained

| Layer | Evidence | What it proves |
| --- | --- | --- |
| Manual/research | Webasto 20/24 manual and cited CARRIER_AC128 references | Documented functions and candidate wire map |
| Baseline corpus | 31 labelled fixed recordings, both checksums valid | Heat/cool/off, setpoints 16–30 °C and wire format |
| Live MVP | Button-by-button remote captures with user display labels | All mode/fan codes, power, temperatures and C/F observations |
| Live auxiliaries | Display, lock, Sleep, clock edits, timer cycles and independent minute edits | Local auxiliary flag/time mapping; rejected captures explicitly retained |
| Production codec | Full-state mutations, integrity/semantic rejection, reserved-field preservation tests | Software command construction and bounded input handling |
| C++ replay | Native g++ build with warnings as errors and undefined-behavior sanitizer, every archived waveform | Deployed C++ wire codec agrees with Python on valid/invalid corpus |
| HA tests | Isolated actual HA entities/services, fake native sender | Setup/reconfigure/reload/unload, IDs, controls, clock refresh on every explicit send, failures, races, availability and persistence |
| ESP firmware | Full bridge compiled for ESP32/ESP-IDF with ESPHome 2026.9.1 | YAML/code generation and firmware linkage |
| Appliance acceptance | Every control sent from Home Assistant to a real AC, 2026-11-18 | The AC accepts and acts on synthesized commands (see below) |

IR timing is approximate and capture distortion is expected. Carrier frequency is
configured at the upstream nominal 38 kHz; the demodulating receiver did not
measure it. Checksums and user labels corroborate accepted frames; rejected frames
are never repaired to fit expectations.

The CI check on 2026-10-14 passed **288 tests**, with
**99.27% integration statement coverage**. Ruff lint/format checks passed, and the
full ESPHome bridge firmware compiled successfully. See GitHub Actions for
checks on the current commit.

## Physical acceptance test (passed 2026-11-18)

The owner tested every control of integration 1.0.6 on a real Webasto Cool Top
Trail air conditioner, through a KinCony ESP32 board (`esp32dev`, IR LED on
GPIO2, IR receiver on GPIO23) running the `esp32/example.yaml` bridge on ESPHome
2026.10.1. The handheld remote was kept at hand to compare. All checks passed.

| Check | Result |
| --- | --- |
| Power off/on | Passed: the AC switches on and off; turning on resumes the selected mode |
| Cool / heat | Passed: the AC runs in the selected mode |
| Dry / fan-only / automatic heat-cool | Passed: each mode is accepted; fan-only has no target temperature |
| Target temperature | Passed: the AC takes the set temperature |
| Fan low/medium/high/auto | Passed: each fan speed is accepted |
| Sleep on/off | Passed |
| Panel display on/off | Passed: the panel display switches off and on |
| Panel control lock on/off | Passed: the panel buttons lock and unlock |
| On/Off timer times and switches | Passed: times and enable switches are accepted |
| Timer execution | Passed: the AC switches at the programmed time (clock set by HA) |
| Handheld remote use | Passed: with the receiver, HA follows the remote's settings |

Home Assistant shows the settings it last sent; IR gives no feedback from the
AC. Disconnect/reconnect, hardware failure, command serialisation and races are
covered by the automated tests above. New results (other models, other boards)
should be added here without rewriting the historical captures.

## Remaining protocol uncertainties

- Byte 7 bit 3: previously called Celsius flag upstream; explicitly contradicted
  by local Celsius and Fahrenheit captures. Preserve as unknown.
- Fahrenheit mapping: captures at 74–78 °F validate rounded Celsius mirror fields;
  C/F switches at 23–25 °C support upward Fahrenheit rounding. Full-range
  endpoint behavior remains reference-derived rather than physically captured.
- Counter high nibble / reserved fields: observed but not understood; preserve.
- ECO: reference flag exists but no remote button/local capability evidence.
- Exact SET TIME value-edit send trigger: entering/selecting alone produced no
  complete capture; a changed value produced a full frame, trigger not isolated.
- Model differences: only the unit above has been tested; other Houghton-made
  models are described by the manual/reference only.
