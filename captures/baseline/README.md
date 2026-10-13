# Imported baseline pulse corpus

`packets.json` contains 31 distinct pulse arrays extracted from the user-provided
[ESPHome baseline](../../esp32/baseline.yaml). Labels come from its mode and
temperature action branches. The OFF button/select share one identical array.

These are existing replay timings, not captures from a newly connected receiver.
Carrier 38 kHz is the YAML's configured frequency, not an optical measurement.
The exact AC/remote model variant, original receiver, capture dates, and before/
after auxiliary settings were not supplied.

Signed durations are microseconds: positive marks, negative spaces. Each array
has 267 durations, preserving both halves, internal gaps, and the final mark.

```bash
python scripts/analyze_ir_baseline.py
```

The script independently validates framing, decodes bits with timing tolerance,
checks both nibble checksums, and reports interpreted fields. See
[the protocol document](../../docs/ir-protocol.md) for confidence and sources.
