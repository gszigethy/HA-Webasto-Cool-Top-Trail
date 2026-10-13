"""Exercise user configuration and rejection of invalid/duplicate entries."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.webasto_cool_top_trail.const import DOMAIN


async def test_user_flow(hass: HomeAssistant) -> None:
    """The UI can create a trimmed, named scaffold."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        f"custom_components.{DOMAIN}.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_NAME: "  Caravan AC  "}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Caravan AC"
    assert result["data"] == {CONF_NAME: "Caravan AC"}


async def test_empty_name(hass: HomeAssistant) -> None:
    """Whitespace is rejected with a field error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_NAME: "  "}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_NAME: "invalid_name"}


@pytest.mark.parametrize("name", ["Caravan AC", " caravan ac "])
async def test_duplicate_name(hass: HomeAssistant, name: str) -> None:
    """Re-adding an existing scaffold does not create duplicate entities."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_NAME: "Caravan AC"})
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_NAME: name}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
