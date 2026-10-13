"""Local native-API transport with serialized, full-state commands."""

import asyncio
import logging
from collections.abc import Callable

from homeassistant.const import (
    EVENT_SERVICE_REGISTERED,
    EVENT_SERVICE_REMOVED,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_RECEIVER,
    CONF_SEND_SERVICE,
    CONF_TEMPERATURE_SENSOR,
    CONF_USE_DEFAULT_STATE,
    DOMAIN,
)
from .protocol import default_frame, interpret_payload, mutate_frame, parse_frame

_LOGGER = logging.getLogger(__name__)


class WebastoBridge:
    """Track commanded state; IR reception cannot prove appliance operation."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.hass = hass
        self.entry = entry
        self.frame: bytes | None = None
        self.source = "unknown"
        self.last_received = None
        self.last_command = None
        self._last_receiver_frame: bytes | None = None
        self._closed = False
        self._revision = 0
        self._lock = asyncio.Lock()
        self._listeners: list[Callable] = []
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")

    @property
    def receiver(self) -> str:
        return self.entry.data[CONF_RECEIVER]

    @property
    def service(self) -> str:
        return self.entry.data[CONF_SEND_SERVICE].removeprefix("esphome.")

    @property
    def connected(self) -> bool:
        state = self.hass.states.get(self.receiver)
        return bool(
            not self._closed
            and state
            and state.state != STATE_UNAVAILABLE
            and self.hass.services.has_service("esphome", self.service)
        )

    @property
    def available(self) -> bool:
        return self.connected and self.frame is not None

    @property
    def state(self) -> dict:
        return interpret_payload(self.frame) if self.frame else {}

    async def async_setup(self) -> None:
        """Restore a template without emitting commands, then listen for frames."""
        saved = await self._store.async_load()
        if saved:
            try:
                self.frame = parse_frame(saved["frame"])
                self.source = "restored"
                if saved.get("last_receiver_frame"):
                    self._last_receiver_frame = parse_frame(
                        saved["last_receiver_frame"]
                    )
            except ValueError, KeyError, TypeError:
                _LOGGER.warning("Ignoring invalid saved IR state")
        if self.frame is None and self.entry.data.get(CONF_USE_DEFAULT_STATE):
            self.frame = default_frame()
            self.source = "default"
        watched = [self.receiver]
        if sensor := self.entry.data.get(CONF_TEMPERATURE_SENSOR):
            watched.append(sensor)
        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, watched, self._state_changed)
        )
        for event in (EVENT_SERVICE_REGISTERED, EVENT_SERVICE_REMOVED):
            self.entry.async_on_unload(
                self.hass.bus.async_listen(event, self._service_changed)
            )
        if state := self.hass.states.get(self.receiver):
            self._receive(state.state)

    @callback
    def _state_changed(self, event) -> None:
        state = event.data.get("new_state")
        if event.data["entity_id"] == self.receiver and state:
            self._receive(state.state)
        self._notify()

    @callback
    def _service_changed(self, event) -> None:
        if event.data.get("domain") == "esphome":
            self._notify()

    @callback
    def _receive(self, value: str) -> None:
        if value in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return
        try:
            frame = parse_frame(value)
        except ValueError:
            _LOGGER.debug("Ignoring invalid or unsupported received IR frame")
            return
        if frame == self._last_receiver_frame:
            return
        self._last_receiver_frame = frame
        self.frame = frame
        self.source = "received"
        self.last_received = dt_util.utcnow()
        self._revision += 1
        self._save()

    @callback
    def _save(self) -> None:
        self._store.async_delay_save(self._storage_data, 1)

    @callback
    def _storage_data(self) -> dict:
        return {
            "frame": self.frame.hex(),
            "last_receiver_frame": self._last_receiver_frame.hex()
            if self._last_receiver_frame
            else None,
        }

    async def async_close(self) -> None:
        """Flush the template on unload without issuing hardware commands."""
        self._closed = True
        if self.frame:
            await self._store.async_save(self._storage_data())

    @callback
    def _notify(self) -> None:
        for listener in tuple(self._listeners):
            listener()

    @callback
    def subscribe(self, listener: Callable) -> Callable:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    async def async_send(self, **changes) -> None:
        """Serialize mutations; failed native-API calls do not advance state."""
        async with self._lock:
            if not self.available:
                raise HomeAssistantError(
                    "Bridge disconnected or no valid frame learned. "
                    "Send a command from the physical remote first."
                )
            try:
                frame = mutate_frame(
                    self.frame, dt_util.now().time().replace(tzinfo=None), **changes
                )
            except ValueError as err:
                raise HomeAssistantError(str(err)) from err
            revision = self._revision
            # The ESPHome action queues IR transmission; it is not an AC acknowledgment.
            try:
                async with asyncio.timeout(10):
                    await self.hass.services.async_call(
                        "esphome",
                        self.service,
                        {"frame": frame.hex(" ").upper()},
                        blocking=True,
                    )
            except TimeoutError as err:
                raise HomeAssistantError(
                    "ESPHome did not confirm the send within 10 seconds; "
                    "the IR command may have been transmitted"
                ) from err
            if self._closed:
                return
            self.last_command = dt_util.utcnow()
            # A newer physical remote command wins over a concurrent outbound request.
            if self._revision == revision:
                self.frame = frame
                self.source = "commanded"
                self._save()
            self._notify()
