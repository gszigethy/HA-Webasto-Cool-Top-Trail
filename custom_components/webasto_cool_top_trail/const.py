"""Integration constants."""

from homeassistant.const import Platform

DOMAIN = "webasto_cool_top_trail"
DEFAULT_NAME = "Webasto Cool Top Trail"
CONF_DEVICE = "device_id"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
PLATFORMS = [
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.TIME,
    Platform.BUTTON,
    Platform.SENSOR,
]
