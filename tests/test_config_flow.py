"""UI setup and transport configuration validation."""

from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.webasto_cool_top_trail.const import DOMAIN

DATA = {
    "name": "Caravan AC",
    "receiver_entity": "sensor.bridge_frame",
    "send_service": "esphome.bridge_send_frame",
}


@pytest.fixture
def transport(hass):
    hass.states.async_set("sensor.bridge_frame", "unknown")
    hass.services.async_register(
        "esphome",
        "bridge_send_frame",
        AsyncMock(),
        schema=vol.Schema({vol.Required("frame"): str}),
    )


async def test_user_flow(hass: HomeAssistant, transport) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    with patch(
        f"custom_components.{DOMAIN}.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**DATA, "name": "  Caravan AC  "}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**DATA, "use_default_state": False}


@pytest.mark.parametrize(
    "changes,error",
    [
        ({"name": "  "}, "invalid_name"),
        ({"send_service": "esphome.missing"}, "invalid_service"),
        ({"receiver_entity": "sensor.missing"}, "invalid_receiver"),
    ],
)
async def test_invalid_input(hass, transport, changes, error):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={**DATA, **changes}
    )
    assert result["type"] is FlowResultType.FORM
    assert error in result["errors"].values()


async def test_duplicate_receiver(hass, transport):
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, version=2)
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={**DATA, "name": "Different name"}
    )
    assert result["reason"] == "already_configured"


async def test_reconfigure(hass, transport):
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, version=2)
    entry.add_to_hass(hass)
    with patch(
        f"custom_components.{DOMAIN}.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
            data={**DATA, "name": "Renamed AC"},
        )
        await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.title == "Renamed AC"


async def test_reconfigure_can_remove_optional_sensor(hass, transport):
    entry = MockConfigEntry(
        domain=DOMAIN, data={**DATA, "temperature_sensor": "sensor.room"}, version=2
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    with patch(
        f"custom_components.{DOMAIN}.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
        await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert "temperature_sensor" not in entry.data


async def test_reject_action_with_wrong_parameters(hass, transport):
    hass.services.async_register(
        "esphome",
        "wrong_send_frame",
        AsyncMock(),
        schema=vol.Schema({vol.Required("command"): str}),
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={**DATA, "send_service": "esphome.wrong_send_frame"},
    )
    assert result["errors"] == {"send_service": "invalid_service"}
