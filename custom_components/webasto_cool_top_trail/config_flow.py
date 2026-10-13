"""UI setup for the integration scaffold."""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import DEFAULT_NAME, DOMAIN


class WebastoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a named scaffold pending a verified IR implementation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an entry; hardware configuration will follow protocol research."""
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            if not name:
                errors[CONF_NAME] = "invalid_name"
            elif any(
                entry.data[CONF_NAME].casefold() == name.casefold()
                for entry in self._async_current_entries()
            ):
                return self.async_abort(reason="already_configured")
            else:
                return self.async_create_entry(title=name, data={CONF_NAME: name})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_NAME, default=DEFAULT_NAME): str}
            ),
            errors=errors,
        )
