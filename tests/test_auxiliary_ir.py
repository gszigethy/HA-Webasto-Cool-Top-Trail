"""Validate independently operated auxiliary controls against live packets."""

import json
from pathlib import Path

from scripts.analyze_ir_baseline import decode_pulses, interpret_payload

RECORDS = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "captures/live/2026-10-13-auxiliary/packets.json"
    ).read_text()
)["records"]


async def test_auxiliary_flags_and_timer_minutes() -> None:
    packets = [decode_pulses(r["pulses_us"]) for r in RECORDS if "decoded" in r]
    states = [interpret_payload(p) for p in packets]
    assert all(s["hvac_mode"] == "heat" for s in states)
    assert all(s["target_temperature_c"] == 24 for s in states)
    assert all(s["fan_mode"] == "auto" for s in states)
    assert {p[13] for p in packets} == {0, 0x40, 0x80}
    assert {bool(p[7] & 2) for p in packets} == {False, True}
    assert {(bool(p[4] & 128), bool(p[5] & 128)) for p in packets} == {
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    }
    assert {p[8] for p in packets} == {0, 1}
    assert {p[9] for p in packets} == {0, 1}
    assert packets[-1][4:6] == bytes([0x09, 0x10])
    assert packets[-1][13] == 0
    assert not states[-1]["sleep"]
