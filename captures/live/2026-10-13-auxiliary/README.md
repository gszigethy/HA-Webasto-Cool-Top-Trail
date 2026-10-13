# Auxiliary remote-button captures — 2026-10-13

Starting and retained HVAC settings: heat, 24 °C, fan auto. Receiver GPIO32;
ESPHome raw timing capture. These observations validate remote commands, not
physical air-conditioner responses. Invalid waveforms are retained explicitly.

| Control | Validated wire effect (zero-based bytes) |
| --- | --- |
| Display | Byte 13 `0x40` disables display; `0x00` restores it |
| Lock | Byte 13 `0x80` enables lock; `0x00` unlocks |
| Sleep | Byte 7 low bit `0x02` enables sleep; clear disables |
| Timer ON | Byte 4 `0x89`: enabled, hour 09; byte 8 minutes |
| Timer OFF | Byte 5 `0x90`: enabled, hour 10; byte 9 minutes |
| Both timers | Bytes 4/5 `0x89`/`0x90` |
| Neither timer | Bytes 4/5 `0x09`/`0x10`: times retained, enables clear |
| ON minute edit | Byte 8 `00 → 01 → 00`, independently edited |
| OFF minute edit | Byte 9 `00 → 01 → 00`, independently edited |

User confirmed four TIMER presses during the blinking selection window:
ON → OFF → both → neither. The final run captured ON, both, and neither;
OFF was missed in that run but separately captured in earlier runs.
Returning to the normal clock after ten seconds does **not** disable a timer:
the steady ON/OFF indicators identify enabled schedules.

SET TIME selects clock hours, then ON time, then OFF time. HOUR/MIN selects
minutes. No complete waveform was captured for entering editing or selecting
minutes without changing a value; this suggests local editing but does not
prove no IR was emitted. Editing the clock minute produced a valid full-state
packet; capture does not distinguish arrow press from edit completion.
The clock-minute restoration waveform was malformed, so restoration has only
user confirmation. Timer-minute increment and restoration pairs were valid.

The final valid packet has both timer enables clear, sleep off, lock off,
display enabled, heat 24 °C, fan auto. No further presses are requested.

Sources: [Webasto manual §§5.5, 5.10–5.13](https://varadicaravan.hu/wp-content/uploads/2022/04/Webasto-Cool-Top-Trail-20_24.pdf)
and [Houghton protocol reference](https://github.com/mrmees/esphome-houghton-ac/blob/master/docs/protocol-spec.md).
The manual describes Lock as disabling the air-distribution panel touch control,
and Display as toggling that panel display. Sleep is supported in heat/cool.
These appliance effects remain untested here.
