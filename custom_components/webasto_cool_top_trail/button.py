"""Explicit clock sync; setup and restarts never send IR automatically."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import WebastoEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([WebastoClockButton(entry.runtime_data, "sync_clock")])


class WebastoClockButton(WebastoEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        await self.bridge.async_send()
