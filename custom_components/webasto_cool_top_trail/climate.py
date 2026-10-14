"""One climate entity for HVAC, target temperature, fans and Sleep."""

import math

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import CONF_TEMPERATURE_SENSOR
from .entity import WebastoEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([WebastoClimate(entry.runtime_data)])


class WebastoClimate(WebastoEntity, ClimateEntity):
    _attr_assumed_state = True
    _attr_name = None
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.HEAT_COOL,
    ]
    _attr_preset_modes = ["none", "sleep"]

    def __init__(self, bridge) -> None:
        super().__init__(bridge, "climate")

    @property
    def temperature_unit(self):
        return (
            UnitOfTemperature.FAHRENHEIT
            if self.bridge.state.get("remote_temperature_unit") == "F"
            else UnitOfTemperature.CELSIUS
        )

    @property
    def min_temp(self):
        return 60 if self.temperature_unit == UnitOfTemperature.FAHRENHEIT else 16

    @property
    def max_temp(self):
        return 86 if self.temperature_unit == UnitOfTemperature.FAHRENHEIT else 30

    @property
    def supported_features(self):
        features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        if self.hvac_mode != HVACMode.FAN_ONLY:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        return features

    @property
    def hvac_mode(self):
        mode = self.bridge.state.get("hvac_mode")
        return HVACMode(mode) if mode else None

    @property
    def target_temperature(self):
        if self.hvac_mode == HVACMode.FAN_ONLY:
            return None
        return self.bridge.state.get(
            "target_temperature_f"
            if self.temperature_unit == UnitOfTemperature.FAHRENHEIT
            else "target_temperature_c"
        )

    @property
    def current_temperature(self):
        sensor = self.bridge.entry.data.get(CONF_TEMPERATURE_SENSOR)
        state = self.hass.states.get(sensor) if sensor else None
        if state is None:
            return None
        try:
            value = float(state.state)
            unit = state.attributes.get("unit_of_measurement")
            if not math.isfinite(value) or unit not in (
                UnitOfTemperature.CELSIUS,
                UnitOfTemperature.FAHRENHEIT,
            ):
                return None
            return TemperatureConverter.convert(value, unit, self.temperature_unit)
        except ValueError, TypeError:
            return None

    @property
    def fan_mode(self):
        return self.bridge.state.get("fan_mode")

    @property
    def fan_modes(self):
        if self.hvac_mode == HVACMode.DRY:
            return ["low"]
        if self.hvac_mode in (HVACMode.FAN_ONLY, HVACMode.HEAT_COOL):
            return ["low", "medium", "high"]
        return ["auto", "low", "medium", "high"]

    @property
    def preset_mode(self):
        return "sleep" if self.bridge.state.get("sleep") else "none"

    async def async_set_hvac_mode(self, hvac_mode) -> None:
        await self.bridge.async_send(hvac_mode=hvac_mode)

    async def async_set_temperature(self, **kwargs) -> None:
        if ATTR_TEMPERATURE not in kwargs:
            raise HomeAssistantError("A single target temperature is required")
        value = kwargs[ATTR_TEMPERATURE]
        if not math.isfinite(value) or not self.min_temp <= value <= self.max_temp:
            raise HomeAssistantError(
                f"Temperature must be between {self.min_temp} and "
                f"{self.max_temp} {self.temperature_unit}"
            )
        # HA converts display units to the current remote profile before this call.
        field = (
            "temperature_f"
            if self.temperature_unit == UnitOfTemperature.FAHRENHEIT
            else "temperature"
        )
        changes = {field: math.floor(value + 0.5)}
        if "hvac_mode" in kwargs:
            changes["hvac_mode"] = kwargs["hvac_mode"]
        await self.bridge.async_send(**changes)

    async def async_set_fan_mode(self, fan_mode) -> None:
        await self.bridge.async_send(fan_mode=fan_mode)

    async def async_set_preset_mode(self, preset_mode) -> None:
        await self.bridge.async_send(preset=preset_mode)

    async def async_turn_off(self) -> None:
        await self.bridge.async_send(hvac_mode="off")

    async def async_turn_on(self) -> None:
        await self.bridge.async_send(
            hvac_mode=self.bridge.state.get("stored_operating_mode", "cool")
        )
