"""Find the bridge's native action and sensors on a selected ESPHome device."""

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

# Names from esp32/bridge.example.yaml; ESPHome keeps them as original names.
RECEIVED_FRAME_NAME = "Received IR frame"
SEND_ACTION = "send_frame"


@dataclass(frozen=True)
class BridgeEndpoints:
    """Native action, optional receiver and every entity of one ESPHome node."""

    service: str
    receiver: str | None
    entities: tuple[str, ...]


def find_endpoints(hass: HomeAssistant, device_id: str) -> BridgeEndpoints | None:
    """Resolve an ESPHome device, or return None if it is not one."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return None
    node = next(
        (
            entry.data["device_name"]
            for entry_id in device.config_entries
            if (entry := hass.config_entries.async_get_entry(entry_id))
            and entry.domain == "esphome"
            and entry.data.get("device_name")
        ),
        None,
    )
    if node is None:
        return None
    entities = [
        entity
        for entity in er.async_entries_for_device(er.async_get(hass), device_id)
        if entity.platform == "esphome"
    ]
    receiver = next(
        (
            entity.entity_id
            for entity in entities
            if entity.domain == "sensor" and entity.original_name == RECEIVED_FRAME_NAME
        ),
        None,
    )
    # Mirrors the ESPHome integration's action naming for a node.
    return BridgeEndpoints(
        f"{node.replace('-', '_')}_{SEND_ACTION}",
        receiver,
        tuple(entity.entity_id for entity in entities),
    )
