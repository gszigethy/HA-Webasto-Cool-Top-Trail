"""Shared stable identity, device metadata, and push subscriptions."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class WebastoEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, bridge, key: str) -> None:
        self.bridge = bridge
        self._attr_unique_id = f"{bridge.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, bridge.entry.entry_id)},
            name=bridge.entry.title,
            manufacturer="Webasto",
            model="Cool Top Trail",
        )

    @property
    def available(self) -> bool:
        return self.bridge.available

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.bridge.subscribe(self.async_write_ha_state))
