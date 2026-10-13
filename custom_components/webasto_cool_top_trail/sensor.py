"""Diagnostic entity for the initial integration scaffold."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, STATUS_AWAITING_PROTOCOL


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Expose development status, without inventing an AC state."""
    async_add_entities([ProtocolStatusSensor(entry)])


class ProtocolStatusSensor(SensorEntity):
    """Report that the protocol and transport still need implementation."""

    _attr_has_entity_name = True
    _attr_translation_key = "protocol_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False
    _attr_options = [STATUS_AWAITING_PROTOCOL]
    _attr_native_value = STATUS_AWAITING_PROTOCOL

    def __init__(self, entry: ConfigEntry) -> None:
        """Use the entry ID until physical bridge identifiers are available."""
        self._attr_unique_id = f"{entry.entry_id}_protocol_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Houghton",
            model="Cool Top Trail (development scaffold)",
        )
