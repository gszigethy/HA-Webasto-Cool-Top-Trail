# Webasto / Houghton CARRIER_AC128 protocol

Status: **baseline and controlled live captures identify `CARRIER_AC128`**.
The production HA/ESPHome implementation constructs complete frames from these
findings. All 31 baseline packets decode to 16 bytes and pass both checksums;
live MVP and auxiliary captures extend the field evidence. Synthesized commands
have not yet been physically tested against the AC. See [validation](validation.md).

The first [live ON/OFF pair](../captures/live/2026-10-13-on-off/README.md) also
matches: the user confirmed 22 C, cooling, auto fan, followed by a second power
button press. Both packets pass both checksums. OFF retains cool/auto/22 and
changes the separate power flag, clock seconds, and second checksum.

## Evidence and provenance

- Local evidence: [sanitized ESPHome baseline](../captures/baseline/baseline.yaml), supplied
  by the user on 2026-10-13, and [31 extracted arrays](../captures/baseline/packets.json).
  Labels come from YAML branches; these are existing replay timings, not new
  recordings or independently verified appliance state.
- Framing comparison: IRremoteESP8266
  [`sendCarrierAC128` / `decodeCarrierAC128`](https://github.com/crankyoldgit/IRremoteESP8266/blob/1e2f0f3ef0a93cbf2a8ddb2e95130f8f4c584b3f/src/ir_Carrier.cpp),
  revision `1e2f0f3ef0a93cbf2a8ddb2e95130f8f4c584b3f`.
- Field comparison: the Houghton ESPHome project's
  [protocol specification](https://github.com/mrmees/esphome-houghton-ac/blob/3c360c92eca4561a288adc81d36f576667796990/docs/protocol-spec.md)
  and [sender/receiver implementation](https://github.com/mrmees/esphome-houghton-ac/blob/3c360c92eca4561a288adc81d36f576667796990/components/carrier_ac128/carrier_ac128.cpp),
  revision `3c360c92eca4561a288adc81d36f576667796990`.
- Further primary reports:
  [Carrier identification #1797](https://github.com/crankyoldgit/IRremoteESP8266/issues/1797),
  [Houghton/RecPro #2009](https://github.com/crankyoldgit/IRremoteESP8266/issues/2009),
  [expanded Houghton analysis #2247](https://github.com/crankyoldgit/IRremoteESP8266/issues/2247).

The protocol name is a library identifier, not proof that this appliance was
manufactured by Carrier. The provided Webasto manual identifies Houghton.
The existing Houghton component is a useful reference, not an automatically
validated replacement for this Webasto variant.

## Why this is CARRIER_AC128

The baseline agrees with the existing implementation in all of these respects:

1. A 128-bit payload in two 64-bit sections, with least-significant bit first
   within each byte.
2. Distinct first/second headers, approximately 20ms section gaps, the middle
   marker, and the final marker: 267 signed durations in the imported arrays.
3. Initial payload byte `0x16`, heat/cool mode nibbles, BCD setpoints, and a
   separate power flag retaining the previous mode while off.
4. Independent nibble-sum checksums for both eight-byte halves: **62/62 pass**.
5. Changing minute/hour/second fields form coherent clock values under the
   published field map.

The second header resembles NEC timings, but that alone does not make this a
NEC command. The complete two-section structure and payload identify the
specific AC protocol. We have compared against source and decoded the local
corpus; we have not run the upstream C++ decoder or tested a newly generated
command on the Webasto unit yet.

## Wire framing and tolerance

Durations below are nominal microseconds from the pinned IRremoteESP8266 source.
The YAML configures a 38kHz carrier; a demodulated receiver log cannot measure
that carrier frequency. Positive raw values denote marks, negative values spaces.

| Segment | Nominal mark / space |
| --- | --- |
| First header | 4600 / 2600 |
| Each bit | 340 / 400 for zero; 340 / 1000 for one |
| After the first 64 bits | 340 / 20600 |
| Middle marker | 4600 / 6700 |
| Second header | 9300 / 5000 |
| After the second 64 bits | 340 / 20600 |
| Final mark | 4600; trailing silence is not included in the stored arrays |

Measured data marks in the imported corpus range **292-429us**, and data spaces
range **343-1004us**. Combined mark+space durations separate into **706-835us**
for zero and **1250-1361us** for one. Receiver distortion can stretch a mark while
shortening its following space, so exact integer matching is inappropriate.

The research decoder checks framing within 25%, short marks within 35%, and
combined bit durations within 20% of 740/1340us. These are explicit research
tolerances, not claimed universal receiver specifications. It rejects ambiguous
durations, wrong polarity, truncation, bad framing, and either bad checksum.
Regression tests include compensated mark/space perturbations of +/-20us on
every baseline packet.

An ESPHome receiver's idle timeout must exceed the internal 20.6ms gap so one
full command remains together. The [capture firmware](../captures/capture-firmware.yaml)
uses 30ms and a 64KB buffer. The configured receiver tolerance applies to
ESPHome protocol matching; the Python research decoder has its own checks.

## Byte map and confidence

Offsets below are **zero-based**; bits use bit 7 as MSB and bit 0 as LSB.
`Observed` means corroborated by the baseline or labelled live remote captures.
`Reference only` means no local button/field variation has confirmed the meaning.
All observations concern transmitted remote settings, not appliance feedback.

| Offset | Meaning / mask | Local evidence |
| --- | --- | --- |
| 0 | Header `0x16` | Observed in all packets |
| 1 | High nibble fan; low nibble mode | All five mode codes and four fan codes locally corroborated |
| 2 | BCD clock minutes | Sequence agrees with the reference map |
| 3 | BCD clock hour | BCD hour corroborated by changing remote clock; baseline `09`/`10` |
| 4 | Timer-on hour BCD in `0x7F`; enable `0x80` | ON hour `09`; enable `0x89` vs disabled `0x09` |
| 5 | Timer-off hour BCD in `0x7F`; enable `0x80` | OFF hour `10`; enable `0x90` vs disabled `0x10` |
| 6 | BCD Celsius setpoint | Every labelled heat/cool value 16-30 matches |
| 7 | Checksum in high nibble; unknown `0x08`, sleep `0x02` | Sleep `0x02` toggled locally; `0x08` unknown: Celsius and Fahrenheit both also use `0x00` |
| 8 | BCD timer-on minutes | Independently edited `00 → 01 → 00` |
| 9 | BCD timer-off minutes | Independently edited `00 → 01 → 00` |
| 10 | Counter high nibble; power low nibble | On `0x08`, off `0x0C`; counter always zero |
| 11 | BCD Fahrenheit setpoint / profile indicator | Zero in Celsius profiles; BCD Fahrenheit target otherwise, validated locally at 74–78 °F |
| 12 | Eco flag `0x04` | Constant zero; reference only; Webasto capability unproven |
| 13 | Panel touch-control lock `0x80`; display disabled `0x40` | Each bit independently toggled in live captures |
| 14 | BCD clock seconds | Sequence agrees with the reference map |
| 15 | Second checksum high nibble; low nibble reserved | Checksum verified; low nibble always zero |

Corroborated fan high-nibble values: `1=auto`, `2=high`, `4=medium`, `8=low`.
Corroborated mode low-nibble values: `1=dry`, `2=cool`, `4=fan_only`, `8=heat`,
`A=heat_cool`. Power is separate from the retained mode nibble.

The reference also reports an alternate on power nibble `0x0`. It is absent
from this corpus. Counter behavior and accepting zero counters still require
controlled Webasto tests; upstream reports should not be treated as proof that
this field can always be discarded.

## Checksums and BCD

For each half `h[0..7]`, preserve the last byte's low nibble and calculate:

```text
checksum = (sum(high_nibble(x) + low_nibble(x) for x in h[0..6])
            + low_nibble(h[7])) modulo 16
h[7] = (checksum << 4) | low_nibble(h[7])
```

Do this independently for offsets 0-7 and 8-15 after every state change.
The upstream IRremoteESP8266 decoder's checksum check is commented out; our
research decoder adds both checks explicitly.

BCD examples: decimal 16 -> `0x16`, 24 -> `0x24`, 30 -> `0x30`. These are not
ordinary binary temperature values. A decoder should reject nibble digits above
9 and validate field-specific ranges before applying received state.

Local worked example, heat 16:

```text
16 18 23 09 10 10 16 F8   00 00 08 00 00 00 30 B0
```

The first half's digit sum including flags is 47 -> checksum `F`. The second is
11 -> checksum `B`. The reference map reads heat, auto fan, 16 C, and 09:23:30.

## Full-state command construction

The complete-state interpretation is supported by the existing Houghton work
and by independent changing clock/mode/temperature/power fields in this corpus.
Both sections belong to one command; they are not separate temperature actions.

A command builder must carry one complete state object: operating mode, power,
fan, temperature/display unit, clock, timers, supported auxiliary flags, and
reserved/counter fields. Change the requested fields, preserve unrelated state,
recalculate both checksums, then encode the complete 16-byte packet LSB-first.

Power-off should retain the previous operating mode and setpoint while updating
the power flags. The local off sample demonstrates heat and 22 C retained.
Changing setpoint must not unexpectedly reset display, lock, sleep, timers, or
unit selection. Serialize/coalesce rapid requests into coherent full packets.

The existing reference component builds Fahrenheit-display packets, clears
timers and resets lock/display settings on transmit. Our implementation preserves
those settings instead. HACS owns the climate entity; ESPHome carries validated
full frames through native API, so there is no duplicate climate controller.
See [technical design](technical-design.md) for mutation rules and transport.

## Remaining evidence gaps

MVP modes/fans/power and auxiliary flags/timers are now locally corroborated.
Further work: full-range physical verification, unknown byte 7 bit 3,
counter behavior, additional remote/model variants, exact clock-edit send trigger,
and optical/appliance acceptance of synthesized commands. Repeated rapid commands
and distinct higher timer digits would broaden the timing/BCD evidence.
See [validation](validation.md). No measured room temperature, compressor action,
or appliance acknowledgment is established by this command stream.

## Reproduce the analysis

```bash
python scripts/analyze_ir_baseline.py
.venv/bin/python -m pytest tests/test_ir_baseline.py
```

See [the decoded baseline table](baseline-decoded.md) for every imported command.
The script handles this complete 267-duration capture layout. A streaming log
collector will additionally need to assemble wrapped log lines and handle
trailing silence, noise, repeats, partial frames, and receiver-specific variation.

`construct_climate_payload` is a research builder for the locally corroborated
Celsius heat/cool/off profile. Starting from a complete heat-16 packet, it can
reconstruct every one of the 31 baseline payloads by changing mode, setpoint,
and clock and recalculating both checksums. `encode_pulses` produces a complete
nominal waveform that decodes back to those payloads. Auxiliary bytes are
preserved. Fahrenheit and additional modes are explicitly outside this builder's
current validation boundary. No generated command has been sent to an appliance.

`scripts/capture_ir_serial.py` assembles wrapped ESPHome raw log lines into
timestamped JSONL records, preserving short/noisy frames even when decoding
fails. The collector uses inactive serial modem lines and emits no IR commands.

## Live MVP validation

See the [button-by-button capture set](../captures/live/2026-10-13-mvp/README.md) for all five modes, four fan settings, on/off, temperature changes, and explicit C/F switching. Byte 7 bit 3 is now reported as unknown rather than Celsius display. Byte 11 changes from BCD 76 in Fahrenheit to zero in Celsius while byte 6 retains BCD 24. Preserve unknown flags; do not infer display units from byte 7 alone.

## Live auxiliary validation

The [auxiliary captures](../captures/live/2026-10-13-auxiliary/README.md)
validate display-disable byte 13 `0x40`, lock byte 13 `0x80`, sleep byte 7
`0x02`, timer enables byte 4/5 `0x80`, and independently edited timer minutes
in bytes 8/9. ON, OFF, both, and neither enable combinations were captured.
Timer times remain stored when disabled. SET TIME and HOUR/MIN navigate local
editing; no complete IR packet was observed for navigation alone. Value edits
produced full-state packets, but the exact send trigger is not yet isolated.
These newer captures supersede the baseline-only evidence column above for
auxiliary fields. Air-conditioner responses are not yet physically verified.

## Production implementation

`custom_components/webasto_cool_top_trail/protocol.py` supplies validated full-state
mutations for all corroborated modes, fans and auxiliaries. It preserves unknown
bits/counter and supports Celsius and Fahrenheit target edits. The earlier
research builder above remains intentionally limited to its baseline profile.
`components/webasto_ir/webasto_ir.h` implements the same wire codec for ESPHome RX/TX, tested with
all archived waveforms. `esp32/example.yaml` exposes native frame actions and
sensors; it never emits commands on boot. [Entity reference](entity-map.md),
[FD](functional-design.md) and [TD](technical-design.md) describe runtime policies.

## Fahrenheit target support

See the [2026-10-14 capture evidence](../captures/live/2026-10-14-fahrenheit/README.md)
for decoded 74–78 °F values, C/F switches, rounding rules and measurement limits.
Native Fahrenheit edits update both temperature fields and both checksums.
