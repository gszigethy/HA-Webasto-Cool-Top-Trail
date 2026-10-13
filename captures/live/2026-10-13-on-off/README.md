# Live ON/OFF capture at 22 C, cool, auto fan

The user pressed ON/OFF to turn the remote on at **22 C, cooling, auto fan**, then
confirmed a second ON/OFF press to turn it off. The receiver observed these two
complete frames on GPIO32. Each contains 267 signed durations and two valid
checksums. GPIO26 transmission was not invoked.

| Command | First eight bytes | Second eight bytes | Receiver time (Europe/Budapest) |
| --- | --- | --- | --- |
| ON | `16 12 38 16 09 10 22 28` | `00 00 08 00 00 00 27 10` | 2026-10-13 16:34:57 |
| OFF | `16 12 38 16 09 10 22 28` | `00 00 0C 00 00 00 40 00` | 2026-10-13 16:35:10 |

The first half is identical. Power byte offset 10 changes from `0x08` to
`0x0C`; stored mode, fan, and setpoint remain cool/auto/22. Clock seconds at
offset 14 change from BCD `0x27` to `0x40`, and the second checksum changes
accordingly. This validates a separate power flag rather than replacing the
stored operating mode with an off code.

The remote clock is approximately 3 minutes 30 seconds ahead of the receiver
timestamps. Preserve the remote clock fields as command data; do not treat them
as the capture time or as appliance feedback.

Original timing values are preserved in [packets.json](packets.json), with
[receiver/firmware metadata](session.json). Source raw logs also include short
noise bursts and unlabelled partial frames, retained privately. They were not
repaired or included as valid protocol evidence.

The exact Webasto AC variant and remote part number are not yet identified.
This verifies receiving and decoding remote commands, not the physical AC's
response to generated commands.
