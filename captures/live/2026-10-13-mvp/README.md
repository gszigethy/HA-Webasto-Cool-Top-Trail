# Button-by-button MVP captures

Captured on 2026-10-13 using GPIO32 RX; no generated IR commands were transmitted.
User observations are retained independently of decoding. Rejected and accidental
steps are explicitly labelled and do not count as confirmed button mappings.

| Step | Button | User observation | Valid payload |
| --- | --- | --- | --- |
| 1 | ON/OFF | pressed, on, 22, auto | `16 12 04 21 09 10 22 78 00 00 08 00 00 00 02 A0` |
| 2 | ON/OFF | pressed, off | `16 12 04 21 09 10 22 78 00 00 0C 00 00 00 41 10` |
| 3 | ON/OFF | pressed, on | `16 12 05 21 09 10 22 88 00 00 08 00 00 00 07 F0` |
| 4 | temperature + | 23 | `16 12 05 21 09 10 23 10 00 00 08 00 00 00 37 20` |
| 5 | temperature - | 22 | `16 12 06 21 09 10 22 10 00 00 08 00 00 00 04 C0` |
| 6 | MODE | dry mode | `16 81 06 21 09 10 24 90 00 00 08 00 00 00 25 F0` |
| 7 | MODE | fan mode, no temperature displayed, fan max level 3; preceding dry mode displayed 24 C | incomplete: received 125 of expected 267 durations; fan mode needs recapture |
| 8 | MODE | heat mode, 24 C, fan auto | `16 18 08 21 09 10 24 B0 00 00 08 00 00 00 42 E0` |
| 9 | MODE | auto mode, 24 C, fan level 3 | `16 2A 09 21 09 10 24 F0 00 00 08 00 00 00 31 C0` |
| 10 | MODE | cool mode, 22 C, fan auto | `16 12 10 21 09 10 22 C0 00 00 08 00 00 00 00 80` |
| 11 | FAN | fan level 1 | `16 82 10 21 09 10 22 30 00 00 08 00 00 00 37 20` |
| 12 | FAN | fan level 2 | 273 durations, rejected by strict decoder; retained for analysis and recapture |
| 13 | FAN | fan level 3 | `16 22 11 21 09 10 22 E0 00 00 08 00 00 00 38 30` |
| 14 | FAN | fan auto | `16 12 12 21 09 10 22 E0 00 00 08 00 00 00 02 A0` |
| 15 | uncontrolled accidental MODE presses | now cooling, 22 C, fan level 1 | uncontrolled sequence; do not assign individual button labels |
| 16 | FAN | fan level 2 | incomplete: 182 of expected 267 durations; needs clean capture |
| 17 | temperature + | 23 C, fan level 2 | `16 42 14 21 09 10 23 40 00 00 08 00 00 00 30 B0` |
| 18 | MODE | dry, 24 C, no fan level displayed | no unique valid packet; raw retained |
| 19 | MODE | fan mode, no temperature displayed, fan level 3 | `16 24 16 21 09 10 24 70 00 00 08 00 00 00 00 80` |
| 20 | Celsius/Fahrenheit | pressed; no unit displayed because fan-only mode | `16 24 17 21 09 10 24 80 00 00 08 76 00 00 28 F0` |
| 21 | MODE | heat mode, 76 F, fan auto | `16 18 18 21 09 10 24 C0 00 00 08 76 00 00 08 D0` |
| 22 | Celsius/Fahrenheit | heat, 24 C, fan auto | `16 18 18 21 09 10 24 C0 00 00 08 00 00 00 46 20` |

## Findings

- All five operating modes are captured: cool, dry, fan-only, heat, automatic heat/cool.
- All four fan codes are captured: auto `1`, high/level 3 `2`, medium/level 2 `4`, low/level 1 `8` in byte 1 high nibble.
- ON/OFF uses byte 10 low nibble `8`/`C`, retaining the operating settings.
- Temperature changes 22 -> 23 -> 22 update byte 6 in BCD.
- Cooling restores its previous setpoint when cycling modes; dry/heat/auto showed 24 C.
- Fan-only hides temperature on the remote but retains BCD 24 in the packet. Dry hides fan level while the packet carries low.
- The published interpretation of byte 7 bit `0x08` as Celsius display is contradicted by this remote: the bit cleared after temperature adjustment while the display stayed Celsius, and remained clear through explicit C/F switches. Preserve it as an unknown flag.
- Explicit Fahrenheit switching populated byte 11 with BCD `76`; switching back to Celsius cleared it to `00`. Byte 6 remained BCD `24` in both. These two unit states are observed; other Fahrenheit values and rounding are not yet tested.
- Both 8-byte nibble checksums validate on every accepted packet. Clock fields also change, so whole-packet comparisons must account for time and checksums.

The research builder still accepts only the original baseline profile and heat/cool/off. This capture set does not constitute appliance acceptance of synthesized commands.
