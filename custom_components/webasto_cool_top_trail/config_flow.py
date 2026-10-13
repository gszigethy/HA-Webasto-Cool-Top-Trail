"""Select existing ESPHome native-API entities and actions through the UI."""

from typing import Any

import probatio
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_RECEIVER,
    CONF_SEND_SERVICE,
    CONF_TEMPERATURE_SENSOR,
    CONF_USE_DEFAULT_STATE,
    DEFAULT_NAME,
    DOMAIN,
)


class WebastoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create or reconfigure one full-frame bridge per receiver entity."""

    VERSION = 2

    def _schema(self, defaults: dict) -> vol.Schema:
        services = [
            f"esphome.{name}"
            for name in self.hass.services.async_services_for_domain("esphome")
            if name.endswith("send_frame")
        ]
        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_RECEIVER, default=defaults.get(CONF_RECEIVER, vol.UNDEFINED)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", integration="esphome"
                    )
                ),
                vol.Required(
                    CONF_SEND_SERVICE,
                    default=defaults.get(CONF_SEND_SERVICE, vol.UNDEFINED),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=services,
                        custom_value=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_USE_DEFAULT_STATE,
                    default=defaults.get(CONF_USE_DEFAULT_STATE, False),
                ): selector.BooleanSelector(),
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

    def _valid_service(self, value: str) -> bool:
        if not value.startswith("esphome."):
            return False
        action = self.hass.services.async_services_for_domain("esphome").get(
            value.removeprefix("esphome.")
        )
        if action is None or action.schema is None:
            return False
        try:
            validated = action.schema({"frame": ""})
        except vol.Invalid, probatio.Invalid:
            return False
        return isinstance(validated, dict) and validated.get("frame") == ""

    async def _configure(self, user_input, reconfigure=False) -> ConfigFlowResult:
        errors = {}
        entry = self._get_reconfigure_entry() if reconfigure else None
        defaults = user_input or (entry.data if entry else {})
        if user_input is not None:
            data = dict(user_input)
            data[CONF_NAME] = data[CONF_NAME].strip()
            data[CONF_SEND_SERVICE] = data[CONF_SEND_SERVICE].strip()
            if not data[CONF_NAME]:
                errors[CONF_NAME] = "invalid_name"
            elif not self._valid_service(data[CONF_SEND_SERVICE]):
                errors[CONF_SEND_SERVICE] = "invalid_service"
            elif not self.hass.states.get(data[CONF_RECEIVER]):
                errors[CONF_RECEIVER] = "invalid_receiver"
            elif any(
                e.data.get(CONF_RECEIVER) == data[CONF_RECEIVER]
                and (not entry or e.entry_id != entry.entry_id)
                for e in self._async_current_entries()
            ):
                return self.async_abort(reason="already_configured")
            else:
                if entry:
                    return self.async_update_reload_and_abort(
                        entry, title=data[CONF_NAME], data=data
                    )
                await self.async_set_unique_id(data[CONF_RECEIVER])
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
