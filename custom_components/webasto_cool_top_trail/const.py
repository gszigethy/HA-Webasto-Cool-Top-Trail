"""Integration constants."""

from homeassistant.const import Platform

DOMAIN = "webasto_cool_top_trail"
DEFAULT_NAME = "Webasto Cool Top Trail"
CONF_RECEIVER = "receiver_entity"
CONF_SEND_SERVICE = "send_service"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
PLATFORMS = [
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.TIME,
    Platform.BUTTON,
    Platform.SENSOR,
]

CONF_USE_DEFAULT_STATE = "use_default_state"
