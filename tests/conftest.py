"""Fixtures for tests using a real Home Assistant test instance."""

import pytest


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load this repository's integration."""
    yield


@pytest.fixture(autouse=True)
def mock_esphome_dependency(hass):
    """Provide native services without starting device discovery."""
    from pytest_homeassistant_custom_component.common import (
        MockModule,
        mock_integration,
    )

    mock_integration(hass, MockModule("esphome"))
