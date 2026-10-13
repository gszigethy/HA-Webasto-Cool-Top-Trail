# Webasto / Houghton IR protocol research

Status: **the supplied pulse corpus matches `CARRIER_AC128`**. This identifies
the wire format; it does not yet prove every feature on the specific Webasto
unit. All 31 baseline packets decode to 16 bytes and pass both checksums.

## Evidence and provenance

- Local evidence: [sanitized ESPHome baseline](../esp32/baseline.yaml), supplied
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
full command remains together. The [capture firmware](../esp32/receiver.example.yaml)
uses 30ms and a 64KB buffer. The configured receiver tolerance applies to
ESPHome protocol matching; the Python research decoder has its own checks.

## Byte map and confidence

Offsets below are **zero-based**; bits use bit 7 as MSB and bit 0 as LSB.
`Observed` means corroborated in this baseline. `Reference only` means the
published Houghton map supplies the semantics, but the feature has not varied
in our local corpus.

| Offset | Meaning / mask | Local evidence |
| --- | --- | --- |
| 0 | Header `0x16` | Observed in all packets |
| 1 | High nibble fan; low nibble mode | Heat `0x18`, cool `0x12`; fan always reference-auto |
| 2 | BCD clock minutes | Sequence agrees with the reference map |
| 3 | BCD clock hour | `09` for heat/cool captures; `10` for off |
| 4 | Timer-on hour BCD in `0x7F`; enable `0x80` | Constant `0x10`; timer semantics reference only |
| 5 | Timer-off hour BCD in `0x7F`; enable `0x80` | Constant `0x10`; reference only |
| 6 | BCD Celsius setpoint | Every labelled heat/cool value 16-30 matches |
| 7 | Checksum in high nibble; Celsius `0x08`, sleep `0x02` | Checksum verified; low nibble always `0x08` |
| 8 | BCD timer-on minutes | Constant zero; reference only |
| 9 | BCD timer-off minutes | Constant zero; reference only |
| 10 | Counter high nibble; power low nibble | On `0x08`, off `0x0C`; counter always zero |
| 11 | BCD Fahrenheit setpoint | Constant zero; reference only |
| 12 | Eco flag `0x04` | Constant zero; reference only; Webasto capability unproven |
| 13 | Lock `0x80`; display disabled `0x40` | Constant zero; reference only |
| 14 | BCD clock seconds | Sequence agrees with the reference map |
| 15 | Second checksum high nibble; low nibble reserved | Checksum verified; low nibble always zero |

Reference fan high-nibble values: `1=auto`, `2=high`, `4=medium`, `8=low`.
Reference mode low-nibble values: `1=dry`, `2=cool`, `4=fan_only`, `8=heat`,
`A=heat_cool`. Only heat/cool/off have local labelled examples.

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

The existing reference component currently builds Fahrenheit-display packets,
clears timers, and resets lock/display settings on transmit. We should reuse
the protocol knowledge while checking those policy choices against this project
and the Webasto model. A native ESPHome climate also enters Home Assistant via
its built-in ESPHome integration; agree the HACS integration boundary before
creating duplicate climate entities.

## Remaining controlled captures

Capture repeated unchanged commands; each fan speed; dry/fan/auto modes; sleep;
display; lock; Celsius/Fahrenheit; distinct timer-on/off times and enables;
power off/on retaining different modes; clock changes; and rapid consecutive
presses. Record the complete remote display before/after each operation.

Test limits from the Webasto manual rather than assuming all Houghton features
are available. No actual room temperature or compressor action is established
by this command stream.

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
