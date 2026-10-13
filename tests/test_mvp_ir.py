"""Independent button labels corroborate the live MVP wire fields."""

import json
from pathlib import Path

import pytest

from scripts.analyze_ir_baseline import decode_pulses, encode_pulses, interpret_payload

RECORDS = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "captures/live/2026-10-13-mvp/packets.json"
    ).read_text()
)["records"]
CAPTURES = {r["step"]: r["capture"] for r in RECORDS if "capture" in r}
EXPECTED = {
    1: ("cool", 22, "auto"),
    2: ("off", 22, "auto"),
    3: ("cool", 22, "auto"),
    4: ("cool", 23, "auto"),
    5: ("cool", 22, "auto"),
    6: ("dry", 24, "low"),
    8: ("heat", 24, "auto"),
    9: ("heat_cool", 24, "high"),
    10: ("cool", 22, "auto"),
    11: ("cool", 22, "low"),
    13: ("cool", 22, "high"),
    14: ("cool", 22, "auto"),
    17: ("cool", 23, "medium"),
    19: ("fan_only", 24, "high"),
    20: ("fan_only", 24, "high"),
    21: ("heat", 24, "auto"),
    22: ("heat", 24, "auto"),
}


@pytest.mark.parametrize("step", EXPECTED)
async def test_mvp_button_fields(step: int) -> None:
    payload = decode_pulses(CAPTURES[step]["pulses_us"])
    state = interpret_payload(payload)
    assert (
        state["hvac_mode"],
        state["target_temperature_c"],
        state["fan_mode"],
    ) == EXPECTED[step]
    assert decode_pulses(encode_pulses(payload)) == payload


async def test_explicit_unit_switch_does_not_change_byte7_bit3() -> None:
    fahrenheit = decode_pulses(CAPTURES[21]["pulses_us"])
    celsius = decode_pulses(CAPTURES[22]["pulses_us"])
    assert fahrenheit[6] == celsius[6] == 0x24
    assert fahrenheit[11] == 0x76
    assert celsius[11] == 0
    assert fahrenheit[7] & 8 == celsius[7] & 8 == 0
