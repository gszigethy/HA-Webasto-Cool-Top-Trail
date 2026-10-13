"""Local recurring timer times, independent of timer enable switches."""

from homeassistant.components.time import TimeEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import WebastoEntity
from .protocol import timer_time


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([WebastoTime(entry.runtime_data, on) for on in (True, False)])


class WebastoTime(WebastoEntity, TimeEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, bridge, on) -> None:
        self.on = on
        super().__init__(bridge, "on_time" if on else "off_time")

    @property
    def native_value(self):
        return timer_time(self.bridge.frame, self.on) if self.bridge.frame else None

    async def async_set_value(self, value) -> None:
        await self.bridge.async_send(**{"on_time" if self.on else "off_time": value})
