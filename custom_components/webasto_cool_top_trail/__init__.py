"""Webasto Cool Top Trail via an ESPHome full-frame IR bridge."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import CONF_RECEIVER, CONF_SEND_SERVICE, PLATFORMS
from .coordinator import WebastoBridge


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load local transport listeners and entity platforms; never transmit on setup."""
    if not entry.data.get(CONF_RECEIVER) or not entry.data.get(CONF_SEND_SERVICE):
        raise ConfigEntryError(
            "Reconfigure this entry to select an ESPHome receiver and send action"
        )
    entry.runtime_data = WebastoBridge(hass, entry)
    await entry.runtime_data.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_close()
        return True
    return False


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Retain scaffold identity; require UI reconfiguration to attach hardware."""
    if entry.version == 1:
        hass.config_entries.async_update_entry(entry, version=2)
    return entry.version == 2


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove our saved template when the user removes the integration entry."""
    from homeassistant.helpers.storage import Store

    from .const import DOMAIN

    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}").async_remove()
