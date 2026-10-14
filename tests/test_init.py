"""Real HA platform lifecycle, identity and no unsolicited IR."""

from unittest.mock import AsyncMock

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.webasto_cool_top_trail.const import DOMAIN

FRAME = "16 18 41 21 09 10 24 80 00 00 08 00 00 00 59 60"


async def setup_bridge(hass, name="Caravan AC", frame=FRAME):
    suffix = name.lower().replace(" ", "_")
    receiver = f"sensor.{suffix}_frame"
    service = f"{suffix}_send_frame"
    hass.states.async_set(receiver, frame)
    send = AsyncMock()
    hass.services.async_register(
        "esphome", service, send, schema=vol.Schema({vol.Required("frame"): str})
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=name,
        version=2,
        data={
            "name": name,
            "receiver_entity": receiver,
            "send_service": f"esphome.{service}",
        },
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
    device = dr.async_get(hass).async_get(entities[0].device_id)
    assert device.manufacturer == "Webasto"
    assert device.model == "Cool Top Trail"
    attributes = hass.states.get("sensor.caravan_ac_protocol_status").attributes
    assert "appliance_feedback" not in attributes
    assert "fahrenheit_temperature_edits_supported" not in attributes
    assert attributes["state_source"] == "received"
    assert attributes["frame"] == FRAME
    assert attributes["last_received"] is not None
    assert attributes["last_command"] is None
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
    hass.states.async_set(entry.runtime_data.receiver, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get("climate.caravan_ac").state == "unavailable"
    send.assert_not_called()


async def test_scaffold_migration_requires_reconfigure(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="Old scaffold", version=1, data={"name": "Old scaffold"}
    )
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.version == 2
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
