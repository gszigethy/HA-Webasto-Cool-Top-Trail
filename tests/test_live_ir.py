"""Validate raw live captures against the user's independent button labels."""

import json
from datetime import time
from pathlib import Path

import pytest

from scripts.analyze_ir_baseline import (
    construct_climate_payload,
    decode_pulses,
    encode_pulses,
    interpret_payload,
)

COMMANDS = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "captures/live/2026-10-13-on-off/packets.json"
    ).read_text()
)["commands"]


@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command["label"])
async def test_live_user_labels(command: dict) -> None:
    """Mode, setpoint, and fan agree with the user's actual remote operation."""
    payload = decode_pulses(command["pulses_us"])
    state = interpret_payload(payload)
    assert state["hvac_mode"] == command["expected_hvac_mode"]
    assert state["target_temperature_c"] == command["expected_target_temperature_c"]
    assert state["fan_mode"] == command["expected_fan_mode"]
    assert decode_pulses(encode_pulses(payload)) == payload


async def test_off_preserves_complete_live_settings() -> None:
    """The full-state builder reproduces the real ON-to-OFF transition."""
    on = decode_pulses(COMMANDS[0]["pulses_us"])
    off = decode_pulses(COMMANDS[1]["pulses_us"])
    assert on[:8] == off[:8]
    assert on[10] == 0x08
    assert off[10] == 0x0C
    generated = construct_climate_payload(
        on, hvac_mode="off", target_temperature_c=22, clock=time(16, 38, 40)
    )
    assert generated == off
