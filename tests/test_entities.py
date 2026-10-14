"""Control real HA entities through services, without contacting any devices."""

import asyncio
from datetime import datetime, time
from unittest.mock import patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.webasto_cool_top_trail.climate import WebastoClimate
from custom_components.webasto_cool_top_trail.protocol import (
    checksum,
    default_frame,
    interpret_payload,
    mutate_frame,
    parse_frame,
)

from .test_init import FRAME, setup_bridge


async def call(hass, domain, action, entity, **data):
    await hass.services.async_call(
        domain, action, {"entity_id": entity, **data}, blocking=True
    )
    await hass.async_block_till_done()


async def test_climate_and_auxiliary_services_preserve_state(hass):
    entry, send = await setup_bridge(hass)
    await call(
        hass, "climate", "set_preset_mode", "climate.caravan_ac", preset_mode="sleep"
    )
    await call(hass, "switch", "turn_on", "switch.caravan_ac_on_timer")
    await call(hass, "time", "set_value", "time.caravan_ac_on_time", time="07:35:00")
    await call(hass, "switch", "turn_on", "switch.caravan_ac_panel_control_lock")
    await call(hass, "switch", "turn_off", "switch.caravan_ac_panel_display")
    await call(hass, "climate", "set_temperature", "climate.caravan_ac", temperature=23)
    frame = parse_frame(send.call_args.args[0].data["frame"])
    assert frame[13] == 0xC0
    assert frame[4] == 0x87 and frame[8] == 0x35
    assert interpret_payload(frame)["sleep"]
    assert frame[6] == 0x23
    assert hass.states.get("time.caravan_ac_on_time").state == "07:35:00"
    assert hass.states.get("switch.caravan_ac_panel_display").state == "off"
    assert entry.runtime_data.source == "commanded"


async def test_power_temperature_and_reload_do_not_turn_on_unexpectedly(hass):
    entry, send = await setup_bridge(hass)
    await call(hass, "climate", "turn_off", "climate.caravan_ac")
    await call(hass, "climate", "set_temperature", "climate.caravan_ac", temperature=23)
    assert hass.states.get("climate.caravan_ac").state == "off"
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.caravan_ac").state == "off"
    assert hass.states.get("climate.caravan_ac").attributes["temperature"] == 23
    assert send.call_count == 2  # No replay at reload; stale receiver value ignored.
    await call(hass, "climate", "turn_on", "climate.caravan_ac")
    assert hass.states.get("climate.caravan_ac").state == "heat"


async def test_failed_send_does_not_update_requested_state(hass):
    entry, send = await setup_bridge(hass)
    send.side_effect = HomeAssistantError("Native API disconnected")
    with pytest.raises(HomeAssistantError):
        await call(hass, "climate", "turn_off", "climate.caravan_ac")
    assert hass.states.get("climate.caravan_ac").state == "heat"
    assert entry.runtime_data.frame == bytes.fromhex(FRAME)
    assert entry.runtime_data.last_command is None


async def test_incoming_remote_wins_over_concurrent_send(hass):
    entry, send = await setup_bridge(hass)
    started, release = asyncio.Event(), asyncio.Event()

    async def delayed(call):
        started.set()
        await release.wait()

    send.side_effect = delayed
    task = asyncio.create_task(entry.runtime_data.async_send(hvac_mode="off"))
    await started.wait()
    incoming = mutate_frame(bytes.fromhex(FRAME), time(21, 50), temperature=22)
    hass.states.async_set(entry.runtime_data.receiver, incoming.hex())
    await hass.async_block_till_done(wait_background_tasks=False)
    release.set()
    await task
    assert entry.runtime_data.frame == incoming
    assert entry.runtime_data.source == "received"


async def test_serialized_commands_do_not_lose_other_changes(hass):
    entry, send = await setup_bridge(hass)
    await asyncio.gather(
        entry.runtime_data.async_send(panel_lock=True),
        entry.runtime_data.async_send(timer_on=True),
    )
    assert entry.runtime_data.state["lock"]
    assert entry.runtime_data.state["timer_on_enabled"]
    assert send.call_count == 2


async def test_modes_presets_and_no_fake_telemetry(hass):
    entry, send = await setup_bridge(hass)
    await call(
        hass, "climate", "set_hvac_mode", "climate.caravan_ac", hvac_mode="fan_only"
    )
    state = hass.states.get("climate.caravan_ac")
    assert state.attributes.get("temperature") is None
    assert state.attributes["current_temperature"] is None
    assert "hvac_action" not in state.attributes
    assert state.attributes["fan_modes"] == ["low", "medium", "high"]
    with pytest.raises(
        HomeAssistantError, match="^Turn on heat or cool before enabling Sleep$"
    ):
        await entry.runtime_data.async_send(preset="sleep")
    with pytest.raises(HomeAssistantError):
        await entry.runtime_data.async_send(temperature=22)
    await call(hass, "climate", "set_hvac_mode", "climate.caravan_ac", hvac_mode="dry")
    assert hass.states.get("climate.caravan_ac").attributes["fan_mode"] == "low"
    with pytest.raises(HomeAssistantError):
        await entry.runtime_data.async_send(fan_mode="high")
    assert send.call_count == 2


async def test_every_explicit_send_refreshes_clock(hass):
    _, send = await setup_bridge(hass)
    actions = (
        ("climate", "set_temperature", "climate.caravan_ac", {"temperature": 23}),
        ("switch", "turn_on", "switch.caravan_ac_panel_display", {}),
        ("time", "set_value", "time.caravan_ac_on_time", {"time": "07:35:00"}),
    )
    for index, (domain, action, entity, data) in enumerate(actions):
        now = datetime(2026, 10, 14, 12 + index, 34, 56)
        with patch(
            "custom_components.webasto_cool_top_trail.coordinator.dt_util.now",
            return_value=now,
        ):
            await call(hass, domain, action, entity, **data)
        frame = parse_frame(send.call_args.args[0].data["frame"])
        assert interpret_payload(frame)["clock"] == now.strftime("%H:%M:%S")
    assert send.call_count == len(actions)


async def test_optional_temperature_sensor_units_and_invalid_values(hass):
    entry, _ = await setup_bridge(hass)
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, "temperature_sensor": "sensor.room"}
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    hass.states.async_set("sensor.room", "77", {"unit_of_measurement": "°F"})
    await hass.async_block_till_done()
    assert hass.states.get("climate.caravan_ac").attributes["current_temperature"] == 25
    for value in ("nan", "not a number"):
        hass.states.async_set("sensor.room", value, {"unit_of_measurement": "°C"})
        await hass.async_block_till_done()
        assert (
            hass.states.get("climate.caravan_ac").attributes["current_temperature"]
            is None
        )


async def test_corrupt_remote_frame_and_fahrenheit_control(hass):
    entry, send = await setup_bridge(hass)
    hass.states.async_set(entry.runtime_data.receiver, "16 00")
    await hass.async_block_till_done()
    assert entry.runtime_data.frame == bytes.fromhex(FRAME)
    fahrenheit = "16 18 18 21 09 10 24 C0 00 00 08 76 00 00 08 D0"
    hass.states.async_set(entry.runtime_data.receiver, fahrenheit)
    await hass.async_block_till_done()
    await call(hass, "climate", "set_temperature", "climate.caravan_ac", temperature=25)
    assert entry.runtime_data.frame[6] == 0x25
    assert entry.runtime_data.frame[11] == 0x77
    await entry.runtime_data.async_send(panel_lock=True)
    assert entry.runtime_data.frame[11] == 0x77
    assert send.call_count == 2


async def test_default_profile_without_startup_transmission(hass):
    entry, send = await setup_bridge(hass, receiver=False)
    assert entry.runtime_data.frame == default_frame()
    assert entry.runtime_data.source == "default"
    assert hass.states.get("climate.caravan_ac").state == "off"
    send.assert_not_called()
    state = hass.states.get("climate.caravan_ac").attributes
    assert (state["temperature"], state["fan_mode"]) == (22, "high")
    await call(hass, "climate", "turn_on", "climate.caravan_ac")
    assert hass.states.get("climate.caravan_ac").state == "heat_cool"
    frame = interpret_payload(parse_frame(send.call_args.args[0].data["frame"]))
    assert (frame["hvac_mode"], frame["fan_mode"]) == ("heat_cool", "high")
    assert frame["target_temperature_c"] == 22


async def test_temperature_service_quantizes_native_celsius_step(hass):
    _, send = await setup_bridge(hass)
    await call(
        hass, "climate", "set_temperature", "climate.caravan_ac", temperature=23.5
    )
    assert parse_frame(send.call_args.args[0].data["frame"])[6] == 0x24


@pytest.mark.parametrize("fan_mode", ["auto", "low", "medium", "high"])
async def test_fan_mode_service(hass, fan_mode):
    _, send = await setup_bridge(hass)
    await call(hass, "climate", "set_fan_mode", "climate.caravan_ac", fan_mode=fan_mode)
    frame = parse_frame(send.call_args.args[0].data["frame"])
    assert interpret_payload(frame)["fan_mode"] == fan_mode
    send.assert_called_once()


@pytest.mark.parametrize(
    "mode,fan_mode",
    [
        ("fan_only", "auto"),
        ("heat_cool", "auto"),
        ("dry", "auto"),
        ("dry", "medium"),
        ("dry", "high"),
    ],
)
async def test_fan_mode_service_rejects_unsupported_speed(hass, mode, fan_mode):
    entry, send = await setup_bridge(hass)
    await call(hass, "climate", "set_hvac_mode", "climate.caravan_ac", hvac_mode=mode)
    frame = entry.runtime_data.frame
    send.reset_mock()
    with pytest.raises(HomeAssistantError):
        await call(
            hass, "climate", "set_fan_mode", "climate.caravan_ac", fan_mode=fan_mode
        )
    assert entry.runtime_data.frame == frame
    send.assert_not_called()


async def test_dry_mode_accepts_low_fan_service(hass):
    _, send = await setup_bridge(hass)
    await call(hass, "climate", "set_hvac_mode", "climate.caravan_ac", hvac_mode="dry")
    send.reset_mock()
    await call(hass, "climate", "set_fan_mode", "climate.caravan_ac", fan_mode="low")
    frame = parse_frame(send.call_args.args[0].data["frame"])
    assert interpret_payload(frame)["fan_mode"] == "low"
    send.assert_called_once()


async def test_temperature_service_changes_mode_in_one_frame(hass):
    _, send = await setup_bridge(hass)
    await call(
        hass,
        "climate",
        "set_temperature",
        "climate.caravan_ac",
        temperature=22,
        hvac_mode="cool",
    )
    send.assert_called_once()
    frame = parse_frame(send.call_args.args[0].data["frame"])
    state = interpret_payload(frame)
    assert state["hvac_mode"] == "cool"
    assert state["target_temperature_c"] == 22


@pytest.mark.parametrize("temperature", [15, 31, float("nan")])
async def test_temperature_service_rejects_invalid_target(hass, temperature):
    entry, send = await setup_bridge(hass)
    with pytest.raises(HomeAssistantError):
        await call(
            hass,
            "climate",
            "set_temperature",
            "climate.caravan_ac",
            temperature=temperature,
        )
    assert entry.runtime_data.frame == bytes.fromhex(FRAME)
    send.assert_not_called()


async def test_fan_only_rejects_temperature_service(hass):
    entry, send = await setup_bridge(hass)
    await call(
        hass, "climate", "set_hvac_mode", "climate.caravan_ac", hvac_mode="fan_only"
    )
    frame = entry.runtime_data.frame
    send.reset_mock()
    with pytest.raises(HomeAssistantError):
        await call(
            hass, "climate", "set_temperature", "climate.caravan_ac", temperature=22
        )
    assert entry.runtime_data.frame == frame
    send.assert_not_called()


@pytest.mark.parametrize("data", [{}, {"temperature": 15}, {"temperature": 31}])
async def test_climate_temperature_guards(hass, data):
    entry, send = await setup_bridge(hass)
    climate = WebastoClimate(entry.runtime_data)
    with pytest.raises(HomeAssistantError, match="required|between 16 and 30"):
        await climate.async_set_temperature(**data)
    assert entry.runtime_data.frame == bytes.fromhex(FRAME)
    send.assert_not_called()


async def test_timeout_does_not_advance_state_or_retry(hass):
    entry, send = await setup_bridge(hass)
    send.side_effect = TimeoutError
    with pytest.raises(HomeAssistantError, match="may have been transmitted"):
        await entry.runtime_data.async_send(hvac_mode="off")
    assert entry.runtime_data.frame == bytes.fromhex(FRAME)
    assert send.call_count == 1


@pytest.mark.parametrize("fahrenheit_display", [False, True])
async def test_fahrenheit_profile_display_and_commands(hass, fahrenheit_display):
    from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

    if fahrenheit_display:
        hass.config.units = US_CUSTOMARY_SYSTEM
    entry, send = await setup_bridge(hass)
    hass.states.async_set(
        entry.runtime_data.receiver, "16 18 18 21 09 10 24 C0 00 00 08 76 00 00 08 D0"
    )
    await hass.async_block_till_done()
    state = hass.states.get("climate.caravan_ac")
    assert state.attributes["temperature"] == (76 if fahrenheit_display else 24.4)
    await call(
        hass,
        "climate",
        "set_temperature",
        "climate.caravan_ac",
        temperature=78 if fahrenheit_display else (78 - 32) * 5 / 9,
    )
    assert entry.runtime_data.frame[11] == 0x78
    assert entry.runtime_data.frame[6] == 0x26
    assert send.call_count == 1


async def test_received_fan_outside_mode_rules_is_shown(hass):
    # Fan-only with auto fan: valid wire data that HA itself would not produce.
    frame = bytearray(bytes.fromhex(FRAME.replace(" ", "")))
    frame[1] = 0x14
    for start in (0, 8):
        frame[start + 7] = (checksum(bytes(frame[start : start + 8])) << 4) | (
            frame[start + 7] & 15
        )
    await setup_bridge(hass, frame=frame.hex(" ").upper())
    state = hass.states.get("climate.caravan_ac")
    assert state.state == "fan_only"
    assert state.attributes["fan_mode"] == "auto"
    assert state.attributes["fan_modes"] == ["auto", "low", "medium", "high"]
