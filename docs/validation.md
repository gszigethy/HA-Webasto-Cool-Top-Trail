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
| ESP firmware | Full bridge compiled for ESP32/ESP-IDF with ESPHome 2026.9.1 | YAML/code generation and firmware linkage; no deployment implied |

IR timing is approximate and capture distortion is expected. Carrier frequency is
configured at the upstream nominal 38 kHz; the demodulating receiver did not
measure it. Checksums and user labels corroborate accepted frames; rejected frames
are never repaired to fit expectations. No synthesized command has yet been
optically verified or accepted by the physical AC in this project.

The pre-release CI check on 2026-10-14 passed **288 tests**, with
**99.27% integration statement coverage**. Ruff lint/format checks passed, and the
full ESPHome bridge firmware compiled successfully. See GitHub Actions for
checks on the current commit. These are software checks, not appliance proof.

## Physical acceptance checklist (not yet performed)

Use a prepared ESP with the actual IR transmitter, powered appliance, and a
receiver where feasible. Keep a known working physical remote available. These
checks are deployment work; they are not performed by CI or against the user's
Home Assistant instance during repository development.

| Check | Expected observation |
| --- | --- |
| Full-state command capture | Synthesized waveform decodes to intended bytes with both checksums |
| Power off/on | Appliance responds; turn-on resumes intended mode |
| Cool / heat | Appliance mode matches command, respecting compressor startup delay in manual |
| Dry / fan-only / automatic heat-cool | Mode accepted; fan-only has no target control; automatic heat-cool uses one setpoint |
| Temperature 16, 22, 23, 24, 30 °C | Appliance accepts setpoints without auxiliary resets |
| Fan low/medium/high/auto | Valid speeds accepted under documented mode constraints |
| Sleep enable/disable | Appliance acknowledges Sleep; long-term temperature program needs separate observation |
| Display and panel lock | Panel display toggles; panel touch control locks/unlocks without changing HVAC |
| ON and OFF times/enables | Independent settings and all four enable combinations accepted; stored times retained |
| Timer execution | Appliance follows programmed time with clock correctly synchronized; HA makes no feedback claim |
| Physical remote use | HA follows captured settings; out-of-range reception remains unobservable |
| Command bursts and echo | No truncation/lost auxiliary changes; self-received commands don't imply AC telemetry |
| Disconnect/reconnect/restart | Entities become unavailable appropriately; reconnect/reload emits no IR |
| Hardware failure | Native action reports local failure; ambiguous timeouts do not automatically retry |

Record exact AC model, remote identifier, ESP board, transmitter drive, receiver
part and pins, firmware/config revision, and observations before declaring a
specific variant appliance-tested. Subsequent successful checks should be stored
as new evidence without rewriting the historical captures.

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
- Appliance behavior for standalone timer recurrence, sleep details, lock/display
  and model differences: manual/reference describe it; remote captures are not
  physical appliance proof.
