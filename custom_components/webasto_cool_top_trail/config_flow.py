"""Select an existing ESPHome bridge device through the UI."""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import CONF_DEVICE, CONF_TEMPERATURE_SENSOR, DEFAULT_NAME, DOMAIN
from .discovery import find_endpoints


class WebastoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create or reconfigure one full-frame bridge per ESPHome device."""

    VERSION = 1

    def _schema(self, defaults: dict) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_DEVICE, default=defaults.get(CONF_DEVICE, vol.UNDEFINED)
                ): selector.DeviceSelector(
                    selector.DeviceSelectorConfig(integration="esphome")
                ),
                vol.Optional(
                    CONF_TEMPERATURE_SENSOR,
                    description={
                        "suggested_value": defaults.get(CONF_TEMPERATURE_SENSOR)
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
            }
        )

    def _is_bridge(self, device_id: str) -> bool:
        endpoints = find_endpoints(self.hass, device_id)
        return endpoints is not None and self.hass.services.has_service(
            "esphome", endpoints.service
        )

    async def _configure(self, user_input, reconfigure=False) -> ConfigFlowResult:
        errors = {}
        entry = self._get_reconfigure_entry() if reconfigure else None
        defaults = user_input or (entry.data if entry else {})
        if user_input is not None:
            data = dict(user_input)
            data[CONF_NAME] = data[CONF_NAME].strip()
            if not data[CONF_NAME]:
                errors[CONF_NAME] = "invalid_name"
            elif not self._is_bridge(data[CONF_DEVICE]):
                errors[CONF_DEVICE] = "not_bridge"
            elif any(
                e.data.get(CONF_DEVICE) == data[CONF_DEVICE]
                and (not entry or e.entry_id != entry.entry_id)
                for e in self._async_current_entries()
            ):
                return self.async_abort(reason="already_configured")
            else:
                if entry:
                    return self.async_update_reload_and_abort(
                        entry,
                        unique_id=data[CONF_DEVICE],
                        title=data[CONF_NAME],
                        data=data,
                    )
                await self.async_set_unique_id(data[CONF_DEVICE])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_NAME], data=data)
        return self.async_show_form(
            step_id="reconfigure" if reconfigure else "user",
            data_schema=self._schema(defaults),
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._configure(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._configure(user_input, reconfigure=True)
