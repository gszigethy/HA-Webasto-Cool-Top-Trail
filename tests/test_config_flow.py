"""UI setup selects an ESPHome bridge device and validates its action."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.webasto_cool_top_trail.const import DOMAIN

from .test_init import add_esphome_bridge


@pytest.fixture
def bridge(hass):
    device_id, _ = add_esphome_bridge(hass)
    return {"name": "Caravan AC", "device_id": device_id}


def no_setup():
    return patch(
        f"custom_components.{DOMAIN}.async_setup_entry",
        new=AsyncMock(return_value=True),
    )


async def test_user_flow(hass: HomeAssistant, bridge) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    with no_setup():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**bridge, "name": "  Caravan AC  "}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == bridge
    assert result["result"].unique_id == bridge["device_id"]


async def test_invalid_name(hass, bridge):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={**bridge, "name": "  "}
    )
    assert result["errors"] == {"name": "invalid_name"}


async def test_rejects_device_without_bridge_action(hass, bridge):
    hass.services.async_remove("esphome", "caravan_ac_bridge_send_frame")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=bridge
    )
    assert result["errors"] == {"device_id": "not_bridge"}


async def test_rejects_non_esphome_device(hass):
    other = MockConfigEntry(domain="demo")
    other.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=other.entry_id, identifiers={("demo", "lamp")}
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"name": "Lamp", "device_id": device.id},
    )
    assert result["errors"] == {"device_id": "not_bridge"}


async def test_duplicate_device(hass, bridge):
    MockConfigEntry(
        domain=DOMAIN, data=bridge, unique_id=bridge["device_id"]
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={**bridge, "name": "Other"}
    )
    assert result["reason"] == "already_configured"


async def test_reconfigure(hass, bridge):
    entry = MockConfigEntry(domain=DOMAIN, data=bridge, unique_id=bridge["device_id"])
    entry.add_to_hass(hass)
    with no_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
            data={**bridge, "name": "Renamed AC"},
        )
        await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.title == "Renamed AC"


async def test_reconfigure_can_remove_optional_sensor(hass, bridge):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**bridge, "temperature_sensor": "sensor.room"},
        unique_id=bridge["device_id"],
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    with no_setup():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], bridge
        )
        await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert "temperature_sensor" not in entry.data


async def test_moving_to_another_device_releases_old_identity(hass, bridge):
    entry = MockConfigEntry(domain=DOMAIN, data=bridge, unique_id=bridge["device_id"])
    entry.add_to_hass(hass)
    new_device, _ = add_esphome_bridge(hass, "Rear AC")
    with no_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
            data={**bridge, "device_id": new_device},
        )
        await hass.async_block_till_done()
        assert result["reason"] == "reconfigure_successful"
        assert entry.unique_id == new_device
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=bridge
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reconfigure_rejects_device_used_by_another_entry(hass, bridge):
    rear, _ = add_esphome_bridge(hass, "Rear AC")
    MockConfigEntry(
        domain=DOMAIN, data={"name": "Rear", "device_id": rear}, unique_id=rear
    ).add_to_hass(hass)
    entry = MockConfigEntry(domain=DOMAIN, data=bridge, unique_id=bridge["device_id"])
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        data={**bridge, "device_id": rear},
    )
    assert result["reason"] == "already_configured"
    assert entry.data["device_id"] == bridge["device_id"]
