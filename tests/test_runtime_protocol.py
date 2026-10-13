"""Production mutations preserve captured unknown/auxiliary state and integrity."""

from datetime import time

import pytest

from custom_components.webasto_cool_top_trail.protocol import (
    checksum,
    decode_pulses,
    default_frame,
    encode_pulses,
    mutate_frame,
    parse_frame,
)


@pytest.mark.parametrize(
    "mode", ["off", "cool", "heat", "dry", "fan_only", "heat_cool"]
)
async def test_all_modes_roundtrip(mode):
    frame = mutate_frame(default_frame(), time(23, 59, 58), hvac_mode=mode)
    assert decode_pulses(encode_pulses(frame)) == frame
    assert frame[2:4] == bytes([0x59, 0x23])
    assert frame[14] == 0x58


async def test_reserved_bits_and_auxiliary_fields_survive_temperature_change():
    seed = bytearray(default_frame())
    seed[7] |= 0x0D  # Unknown low bits, including the unreliable unit bit.
    seed[12] = 0xA5  # Includes unimplemented ECO and unknown bits.
    seed[13] = 0xC3
    seed[10] = 0xAC
    seed[15] |= 3
    for start in (0, 8):
        seed[start + 7] = (checksum(bytes(seed[start : start + 8])) << 4) | (
            seed[start + 7] & 15
        )
    frame = mutate_frame(bytes(seed), time(3, 4, 5), temperature=22)
    assert frame[7] & 15 == seed[7] & 15
    assert frame[15] & 15 == 3
    assert frame[12:14] == seed[12:14]
    assert frame[10] == 0xAC  # Remains off, counter preserved.


@pytest.mark.parametrize(
    "changes",
    [
        {"temperature": 31},
        {"temperature": 15},
        {"temperature": 22.5},
        {"temperature": float("nan")},
        {"temperature": True},
        {"fan_mode": "invalid"},
        {"hvac_mode": "auto"},
        {"preset": "eco"},
        {"display": 1},
        {"on_time": time(12, 0, 1)},
        {"off_time": "12:00"},
        {"unknown_setting": True},
    ],
)
async def test_invalid_commands_are_rejected(changes):
    with pytest.raises(ValueError):
        mutate_frame(default_frame(), time(12), **changes)


async def test_semantic_validation_rejects_valid_checksum_invalid_clock():
    frame = bytearray(default_frame())
    frame[2] = 0x60
    frame[7] = checksum(bytes(frame[:8])) << 4
    with pytest.raises(ValueError, match="clock"):
        parse_frame(frame.hex())


async def test_turn_off_preserves_sleep_and_operating_mode():
    heat = mutate_frame(default_frame(), time(12), hvac_mode="heat", preset="sleep")
    off = mutate_frame(heat, time(12, 1), hvac_mode="off")
    assert off[1] == heat[1]
    assert off[7] & 2
    assert off[10] & 15 == 12
