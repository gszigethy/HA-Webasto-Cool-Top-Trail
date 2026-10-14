# Fahrenheit capture session — 2026-10-14

Heat mode, fan auto, otherwise unchanged settings. `packets.json` retains complete
waveforms, timestamps, labels and decoder results; malformed recordings remain
as negative evidence. No raw serial identifiers are included.

| Operation / displayed state | Byte 6, Celsius BCD | Byte 11, Fahrenheit BCD |
| --- | --- | --- |
| Switch from 24 °C: 76 °F | 24 | 76 |
| UP: 77 °F | 25 | 77 |
| UP: 78 °F | 26 | 78 |
| Switch: 26 °C | 26 | 00 |
| DOWN: 25 °C | 25 | 00 |
| Switch: 77 °F | 25 | 77 |
| DOWN: 76 °F | 24 | 76 |
| Switch: 24 °C | 24 | 00 |
| DOWN: 23 °C | 23 | 00 |
| Switch: 74 °F | 23 | 74 |
| UP: 75 °F | 24 | 75 |
| UP: 76 °F | 24 | 76 |
| Switch: 24 °C | 24 | 00 |

The final reported 24 °C → 76 °F switch had an incomplete waveform; it is not
counted as independent decoded confirmation. One earlier 77 °F press had a bad
header; a later repeat was valid. The first DOWN report had no complete frame.

The observations support these rules: Fahrenheit target edits carry the exact
integer F value and a Celsius mirror `floor((F−32)×5/9+0.5)`. Switching Celsius
to Fahrenheit uses `ceil(C×9/5+32)`, demonstrated at 23, 24 and 25 °C. This is
an inference from those values, not a measurement of every setpoint. Byte 7's
unknown low bit remains preserved and is not used as a unit flag. Byte 11 zero
identifies Celsius profiles in these recordings.

Control accepts 60–86 °F, the reference protocol range, with endpoints tested
in software rather than measured on this remote. No synthesized frame has yet
been verified against the appliance. The climate entity adopts the learned
profile's native unit and 1-degree step; HA converts to its preferred display
unit. There is no separate C/F selector. Power, fan and auxiliary changes retain
the existing target fields. ESPHome transports the same complete 16-byte frames.
