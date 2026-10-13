"""Verify that ESPHome's wrapped logs retain complete timing evidence."""

import json
from pathlib import Path

from scripts.capture_ir_serial import RawLogAssembler, describe_frame

PULSES = json.loads(
    (Path(__file__).resolve().parents[1] / "captures/baseline/packets.json").read_text()
)["commands"][0]["pulses_us"]


async def test_wrapped_raw_dump() -> None:
    """Colored chunked ESPHome logs assemble into the original packet."""
    assembler = RawLogAssembler()
    frames = []
    for start in range(0, len(PULSES), 20):
        prefix = "Received Raw: " if start == 0 else "  "
        data = ", ".join(str(value) for value in PULSES[start : start + 20])
        frames.extend(
            assembler.feed(f"\x1b[0;32m[I][remote.raw:028]: {prefix}{data}\x1b[0m")
        )
    assert frames == [PULSES]
    assert assembler.flush() == []
    record = describe_frame(frames[0], "off_button")
    assert record["pulses_us"] == PULSES
    assert record["decoded"]["hvac_mode"] == "off"


async def test_partial_and_noise_preserved() -> None:
    """Short/noisy frames survive storage even when decoding fails."""
    assembler = RawLogAssembler()
    assert assembler.feed("[I][remote.raw:028]: Received Raw: 340, -400, 340") == []
    assert assembler.feed("[D][other:001]: unrelated output 123") == []
    frames = assembler.feed("[I][remote.raw:028]: Received Raw: 400, -500, 400")
    assert frames == [[340, -400, 340]]
    assert assembler.flush() == [[400, -500, 400]]
    record = describe_frame(frames[0], "noise")
    assert record["pulses_us"] == frames[0]
    assert "decode_error" in record


async def test_orphan_continuation_ignored() -> None:
    """Connecting mid-dump cannot produce a fabricated complete frame."""
    assembler = RawLogAssembler()
    assert assembler.feed("[I][remote.raw:028]:   340, -400, 340") == []
    assert assembler.flush() == []
