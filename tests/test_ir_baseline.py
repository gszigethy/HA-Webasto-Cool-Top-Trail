"""Capture-backed research regression tests, separate from hardware proof."""

import json
from datetime import time
from pathlib import Path

import pytest

from scripts.analyze_ir_baseline import (
    construct_climate_payload,
    decode_pulses,
    encode_pulses,
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
    assert state["unknown_byte7_bit3"] is True
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


@pytest.mark.parametrize("command", CORPUS, ids=lambda command: command["label"])
async def test_construct_all_golden_packets(command: dict) -> None:
    """One complete seed reconstructs every distinct captured baseline payload."""
    seed = decode_pulses(CORPUS[1]["pulses_us"])  # heat_16
    expected = decode_pulses(command["pulses_us"])
    state = interpret_payload(expected)
    generated = construct_climate_payload(
        seed,
        hvac_mode=command["hvac_mode"],
        target_temperature_c=state["target_temperature_c"],
        clock=time.fromisoformat(state["clock"]),
    )
    assert generated == expected
    assert decode_pulses(encode_pulses(generated)) == expected


@pytest.mark.parametrize("mode,temp", [("dry", 22), ("heat", 15), ("cool", 31)])
async def test_builder_rejects_unvalidated_parameters(mode: str, temp: int) -> None:
    """Research support boundaries are explicit, not silently coerced."""
    seed = decode_pulses(CORPUS[1]["pulses_us"])
    with pytest.raises(ValueError):
        construct_climate_payload(
            seed, hvac_mode=mode, target_temperature_c=temp, clock=time(12)
        )


async def test_builder_preserves_auxiliary_state() -> None:
    """Changing climate settings keeps nonzero timers from a reference packet."""
    # Independent Carrier reference packet from IRremoteESP8266 issue #2247;
    # not a locally captured Webasto command. Timers are deliberately nonzero.
    template = bytes.fromhex("16 22 38 00 93 91 25 B8 11 22 08 00 00 00 00 E0")
    generated = construct_climate_payload(
        template, hvac_mode="heat", target_temperature_c=24, clock=time(3, 29, 1)
    )
    validate_payload(generated)
    for index in (0, 4, 5, 8, 9, 11, 12, 13):
        assert generated[index] == template[index]
    assert generated[1] & 0xF0 == template[1] & 0xF0
    assert generated[7] & 0x0F == template[7] & 0x0F
    assert generated[10] & 0xF0 == template[10] & 0xF0
    assert generated[15] & 0x0F == template[15] & 0x0F


async def test_fahrenheit_reference_not_silently_rewritten() -> None:
    """The research builder cannot leave a conflicting Fahrenheit setpoint."""
    template = bytes.fromhex("16 81 42 06 00 00 24 20 00 00 68 76 00 00 02 D0")
    with pytest.raises(ValueError, match="Celsius-only"):
        construct_climate_payload(
            template, hvac_mode="heat", target_temperature_c=22, clock=time(12)
        )
