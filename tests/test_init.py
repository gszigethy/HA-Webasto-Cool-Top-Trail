"""Real HA platform lifecycle, identity and no unsolicited IR."""

from unittest.mock import AsyncMock

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.webasto_cool_top_trail.const import DOMAIN

FRAME = "16 18 41 21 09 10 24 80 00 00 08 00 00 00 59 60"


def add_esphome_bridge(hass, name="Caravan AC", frame=FRAME, receiver=True):
    """Register an ESPHome node like bridge.example.yaml: device, sensors, action."""
    suffix = name.lower().replace(" ", "_")
    node = f"{suffix.replace('_', '-')}-bridge"
    esphome = MockConfigEntry(
        domain="esphome", data={"device_name": node}, unique_id=node
    )
    esphome.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=esphome.entry_id,
        identifiers={("esphome", node)},
        name=f"{name} bridge",
    )
    registry = er.async_get(hass)
    sensors = [("Transmitted IR frame", f"{suffix}_transmitted", "unknown")]
    if receiver:
        sensors.append(("Received IR frame", f"{suffix}_frame", frame))
    for original_name, object_id, state in sensors:
        entity = registry.async_get_or_create(
            "sensor",
            "esphome",
            f"{node}-{object_id}",
            config_entry=esphome,
            device_id=device.id,
            original_name=original_name,
            suggested_object_id=object_id,
        )
        hass.states.async_set(entity.entity_id, state)
    send = AsyncMock()
    hass.services.async_register(
        "esphome",
        f"{node.replace('-', '_')}_send_frame",
        send,
        schema=vol.Schema({vol.Required("frame"): str}),
    )
    return device.id, send


async def setup_bridge(hass, name="Caravan AC", frame=FRAME, receiver=True):
    device_id, send = add_esphome_bridge(hass, name, frame, receiver)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=name,
        unique_id=device_id,
        data={"name": name, "device_id": device_id},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, send


async def test_setup_reload_unload(hass):
    entry, send = await setup_bridge(hass)
    assert entry.state is ConfigEntryState.LOADED
    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) == 8
    assert hass.states.get("climate.caravan_ac").state == "heat"
    send.assert_not_called()
    ids = {e.entity_id for e in entities}
    assert len({e.device_id for e in entities}) == 1
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert {
        e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    } == ids
    send.assert_not_called()
    bridge = entry.runtime_data
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.caravan_ac").state == "unavailable"
    assert bridge._listeners == []


async def test_multiple_entries(hass):
    front, _ = await setup_bridge(hass, "Front AC")
    rear, _ = await setup_bridge(hass, "Rear AC")
    assert await hass.config_entries.async_unload(front.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.rear_ac").state == "heat"
    assert rear.runtime_data.available


async def test_no_frame_and_disconnect(hass):
    entry, send = await setup_bridge(hass, frame="unknown")
    assert hass.states.get("climate.caravan_ac").state == "unavailable"
    assert (
        hass.states.get("sensor.caravan_ac_protocol_status").state == "awaiting_frame"
    )
    hass.states.async_set(entry.runtime_data.receiver, FRAME)
    await hass.async_block_till_done()
    assert hass.states.get("climate.caravan_ac").state == "heat"
    # ESPHome marks every entity of an offline node unavailable.
    for entity_id in entry.runtime_data.endpoints.entities:
        hass.states.async_set(entity_id, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get("climate.caravan_ac").state == "unavailable"
    assert hass.states.get("sensor.caravan_ac_protocol_status").state == (
        "disconnected"
    )
    send.assert_not_called()


async def test_transmitter_only_starts_from_default_profile(hass):
    entry, send = await setup_bridge(hass, receiver=False)
    bridge = entry.runtime_data
    assert bridge.receiver is None
    assert bridge.source == "default"
    assert hass.states.get("climate.caravan_ac").state == "off"
    hass.services.async_remove("esphome", bridge.service)
    await hass.async_block_till_done()
    assert hass.states.get("climate.caravan_ac").state == "unavailable"
    send.assert_not_called()


async def test_missing_device_requires_reconfigure(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="Gone", data={"name": "Gone", "device_id": "missing"}
    )
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert not hass.states.async_all("climate")


async def test_remove_entry_cleans_saved_frame(hass, hass_storage):
    entry, _ = await setup_bridge(hass)
    key = f"{DOMAIN}.{entry.entry_id}"
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert key in hass_storage
    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert key not in hass_storage
