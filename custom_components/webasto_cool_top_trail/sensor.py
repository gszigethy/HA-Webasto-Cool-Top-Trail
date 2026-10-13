"""Honest transport/command diagnostics rather than invented AC feedback."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import WebastoEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([WebastoStatus(entry.runtime_data, "protocol_status")])


class WebastoStatus(WebastoEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_options = ["awaiting_frame", "ready", "disconnected"]

    @property
    def available(self):
        return True

    @property
    def native_value(self):
        if not self.bridge.connected:
            return "disconnected"
        return "ready" if self.bridge.frame else "awaiting_frame"

    @property
    def extra_state_attributes(self):
        return {
            "state_source": self.bridge.source,
            "last_received": self.bridge.last_received,
            "last_command": self.bridge.last_command,
            "appliance_feedback": False,
            "frame": self.bridge.frame.hex(" ").upper() if self.bridge.frame else None,
            "fahrenheit_temperature_edits_supported": False,
        }
