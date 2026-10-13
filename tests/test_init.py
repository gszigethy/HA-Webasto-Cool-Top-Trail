"""Verify entity registration, reload, multiple entries, and clean unloading."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_NAME, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.webasto_cool_top_trail.const import (
    DOMAIN,
    STATUS_AWAITING_PROTOCOL,
)


async def test_setup_reload_unload(hass: HomeAssistant) -> None:
    """The scaffold has honest state and stable IDs throughout its lifecycle."""
    entry = MockConfigEntry(
        domain=DOMAIN, title="Caravan AC", data={CONF_NAME: "Caravan AC"}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) == 1
    entity = entities[0]
    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == STATUS_AWAITING_PROTOCOL
    assert hass.states.async_all("climate") == []
    assert entity.device_id is not None
    device = dr.async_get(hass).async_get(entity.device_id)
    assert device is not None
    assert device.identifiers == {(DOMAIN, entry.entry_id)}

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    reloaded = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert [item.entity_id for item in reloaded] == [entity.entity_id]
    assert hass.states.get(entity.entity_id).state == STATUS_AWAITING_PROTOCOL

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert hass.states.get(entity.entity_id).state == STATE_UNAVAILABLE


async def test_multiple_entries(hass: HomeAssistant) -> None:
    """Separate named units have independent entities and unload independently."""
    entries = [
        MockConfigEntry(domain=DOMAIN, title=name, data={CONF_NAME: name})
        for name in ("Front AC", "Rear AC")
    ]
    for entry in entries:
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    front, rear = [
        er.async_entries_for_config_entry(registry, entry.entry_id)[0]
        for entry in entries
    ]
    assert front.unique_id != rear.unique_id
    assert front.device_id != rear.device_id
    assert await hass.config_entries.async_unload(entries[0].entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(rear.entity_id).state == STATUS_AWAITING_PROTOCOL
