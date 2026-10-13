"""Auxiliary switches for display, touch controls, and timer enables."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import WebastoEntity

KEYS = {
    "display": "display_enabled",
    "panel_lock": "lock",
    "timer_on": "timer_on_enabled",
    "timer_off": "timer_off_enabled",
}


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([WebastoSwitch(entry.runtime_data, key) for key in KEYS])


class WebastoSwitch(WebastoEntity, SwitchEntity):
    _attr_assumed_state = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, bridge, key) -> None:
        super().__init__(bridge, key)
        self.key = key

    @property
    def is_on(self):
        return self.bridge.state.get(KEYS[self.key])

    async def async_turn_on(self, **kwargs) -> None:
        await self.bridge.async_send(**{self.key: True})

    async def async_turn_off(self, **kwargs) -> None:
        await self.bridge.async_send(**{self.key: False})
