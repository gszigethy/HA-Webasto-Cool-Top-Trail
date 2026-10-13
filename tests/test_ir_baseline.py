"""Capture-backed research regression tests, separate from hardware proof."""

import json
from pathlib import Path

import pytest

from scripts.analyze_ir_baseline import (
    decode_pulses,
    from_bcd,
    interpret_payload,
    validate_payload,
)

CORPUS = json.loads(
    (Path(__file__).resolve().parents[1] / "captures/baseline/packets.json").read_text()
)["commands"]


@pytest.mark.parametrize("command", CORPUS, ids=lambda command: command["label"])
async def test_baseline_fields(command: dict) -> None:
    """All recordings agree with their independent YAML mode/setpoint labels."""
    payload = decode_pulses(command["pulses_us"])
    state = interpret_payload(payload)
    assert state["hvac_mode"] == command["hvac_mode"]
    if command["target_temperature_c"] is not None:
        assert state["target_temperature_c"] == command["target_temperature_c"]
    assert state["fan_mode"] == "auto"
    assert state["celsius_display"] is True
    assert state["timer_on_enabled"] is False
    assert state["timer_off_enabled"] is False


@pytest.mark.parametrize("excess", [-20, 20])
@pytest.mark.parametrize("command", CORPUS, ids=lambda command: command["label"])
async def test_receiver_mark_space_distortion(command: dict, excess: int) -> None:
    """Mark stretch/space shrink retains the payload across the entire corpus."""
    original = command["pulses_us"]
    perturbed = [
        duration + excess for duration in original
    ]  # Negative spaces shrink when positive marks grow.
    assert decode_pulses(perturbed) == decode_pulses(original)


async def test_off_golden_bytes() -> None:
    """An off command preserves its stored mode and setpoint."""
    payload = decode_pulses(CORPUS[0]["pulses_us"])
    assert payload.hex(" ") == "16 18 05 10 10 10 22 48 00 00 0c 00 00 00 29 70"
    state = interpret_payload(payload)
    assert state["hvac_mode"] == "off"
    assert state["stored_operating_mode"] == "heat"
    assert state["target_temperature_c"] == 22
    assert state["clock"] == "10:05:29"


@pytest.mark.parametrize("index", range(16))
async def test_corruption_rejected(index: int) -> None:
    """A single changed nibble cannot bypass the header/checksum checks."""
    payload = bytearray(decode_pulses(CORPUS[0]["pulses_us"]))
    payload[index] ^= 1
    with pytest.raises(ValueError):
        validate_payload(bytes(payload))


@pytest.mark.parametrize("change", ["truncated", "polarity", "framing", "ambiguous"])
async def test_bad_timings_rejected(change: str) -> None:
    """Malformed input is rejected rather than interpreted as state."""
    pulses = CORPUS[0]["pulses_us"].copy()
    if change == "truncated":
        pulses.pop()
    elif change == "polarity":
        pulses[3] = abs(pulses[3])
    elif change == "framing":
        pulses[0] = 100
    else:
        pulses[2:4] = [340, -660]  # Between both accepted bit-duration bands.
    with pytest.raises(ValueError):
        decode_pulses(pulses)


async def test_invalid_bcd_rejected() -> None:
    """Invalid decimal digits are not silently accepted."""
    with pytest.raises(ValueError, match="BCD"):
        from_bcd(0x1A)
