"""CARRIER_AC128 wire codec and conservative full-state command mutations."""

import math
from collections.abc import Sequence
from datetime import time

# Nominals from IRremoteESP8266 ir_Carrier.cpp, cited in docs/ir-protocol.md.
FRAMING = {
    0: 4600,
    1: 2600,
    130: 340,
    131: 20600,
    132: 4600,
    133: 6700,
    134: 9300,
    135: 5000,
    264: 340,
    265: 20600,
    266: 4600,
}
MODES = {0x1: "dry", 0x2: "cool", 0x4: "fan_only", 0x8: "heat", 0xA: "heat_cool"}
FANS = {0x1: "auto", 0x2: "high", 0x4: "medium", 0x8: "low"}


def matches(value: int, nominal: int, tolerance: float = 0.25) -> bool:
    """Match a duration using a relative tolerance, never exact equality."""
    return nominal * (1 - tolerance) <= value <= nominal * (1 + tolerance)


def checksum(half: bytes) -> int:
    """Return the checksum nibble for an eight-byte half."""
    if len(half) != 8:
        raise ValueError("A checksum half must contain eight bytes")
    return (
        sum((byte >> 4) + (byte & 0xF) for byte in half[:7]) + (half[7] & 0xF)
    ) & 0xF


def validate_payload(payload: bytes) -> None:
    """Validate the header and independent nibble checksums."""
    if len(payload) != 16 or payload[0] != 0x16:
        raise ValueError("Expected a 16-byte CARRIER_AC128 payload starting with 0x16")
    for start in (0, 8):
        half = payload[start : start + 8]
        if checksum(half) != half[7] >> 4:
            raise ValueError(f"Invalid checksum in section {start // 8 + 1}")


def decode_pulses(pulses: Sequence[int]) -> bytes:
    """Decode the baseline's two-section layout using combined bit durations."""
    if len(pulses) != 267:
        raise ValueError("Expected 267 signed durations, including the final mark")
    for index, duration in enumerate(pulses):
        if type(duration) is not int or duration == 0:
            raise ValueError(f"Invalid duration at index {index}")
        if (duration > 0) != (index % 2 == 0):
            raise ValueError(f"Unexpected mark/space polarity at index {index}")
    for index, nominal in FRAMING.items():
        # Short marks have more receiver-dependent variation than the long framing.
        tolerance = 0.35 if nominal == 340 else 0.25
        if not matches(abs(pulses[index]), nominal, tolerance):
            raise ValueError(f"Unrecognized framing duration at index {index}")

    decoded = bytearray()
    for start in (2, 136):
        bits = []
        for index in range(start, start + 128, 2):
            mark, space = pulses[index], -pulses[index + 1]
            if not matches(mark, 340, 0.35):
                raise ValueError(f"Unrecognized data mark at index {index}")
            # Demodulators can stretch a mark while shortening its following space.
            # Checking the total tolerates that distortion without broad bit overlap.
            total = mark + space
            candidates = [
                bit
                for bit, nominal in ((0, 740), (1, 1340))
                if matches(total, nominal, 0.20)
            ]
            if len(candidates) != 1:
                raise ValueError(f"Unrecognized or ambiguous bit at index {index}")
            bits.append(candidates[0])
        decoded.extend(
            sum(bit << offset for offset, bit in enumerate(bits[index : index + 8]))
            for index in range(0, 64, 8)
        )
    payload = bytes(decoded)
    validate_payload(payload)
    return payload


def from_bcd(value: int) -> int:
    """Decode a BCD byte, rejecting impossible decimal digits."""
    if not 0 <= value <= 255 or value >> 4 > 9 or value & 0xF > 9:
        raise ValueError("Invalid BCD value")
    return (value >> 4) * 10 + (value & 0xF)


def encode_pulses(payload: bytes) -> list[int]:
    """Encode a validated complete state using the cited nominal wire timings."""
    validate_payload(payload)
    pulses = []
    for start, header in ((0, (4600, -2600)), (8, (9300, -5000))):
        pulses.extend(header)
        for byte in payload[start : start + 8]:
            for bit in range(8):
                pulses.extend((340, -1000 if byte & (1 << bit) else -400))
        pulses.extend((340, -20600, 4600))
        if start == 0:
            pulses.append(-6700)
    return pulses


def interpret_payload(payload: bytes) -> dict:
    """Interpret fields using the cited map, without claiming device feedback."""
    validate_payload(payload)
    mode = MODES.get(payload[1] & 0xF)
    power_flags = payload[10] & 0xF
    if power_flags == 0xC:
        hvac_mode = "off"
    elif power_flags in (0x0, 0x8):
        hvac_mode = mode
    else:
        hvac_mode = None
    return {
        "hex": payload.hex(" ").upper(),
        "hvac_mode": hvac_mode,
        "stored_operating_mode": mode,
        "fan_mode": FANS.get(payload[1] >> 4),
        "target_temperature_c": from_bcd(payload[6]),
        "target_temperature_f": from_bcd(payload[11]) if payload[11] else None,
        "remote_temperature_unit": "F" if payload[11] else "C",
        "clock": ":".join(f"{from_bcd(payload[index]):02}" for index in (3, 2, 14)),
        "power_flags": power_flags,
        "counter_nibble": payload[10] >> 4,
        "unknown_byte7_bit3": bool(payload[7] & 0x8),
        "sleep": bool(payload[7] & 0x2),
        "eco": bool(payload[12] & 0x4),
        "lock": bool(payload[13] & 0x80),
        "display_enabled": not bool(payload[13] & 0x40),
        "timer_on_enabled": bool(payload[4] & 0x80),
        "timer_off_enabled": bool(payload[5] & 0x80),
    }


def to_bcd(value: int) -> int:
    """Encode an integer decimal value."""
    return ((value // 10) << 4) | (value % 10)


def parse_frame(frame: str) -> bytes:
    """Validate wire integrity and the fields required for safe control."""
    payload = bytes.fromhex(frame)
    validate_payload(payload)
    if payload[1] & 15 not in MODES or payload[1] >> 4 not in FANS:
        raise ValueError("Unsupported mode or fan code")
    if payload[10] & 15 not in (0, 8, 12):
        raise ValueError("Unsupported power code")
    if not 16 <= from_bcd(payload[6]) <= 30:
        raise ValueError("Unsupported Celsius setpoint")
    for index, maximum in ((2, 59), (3, 23), (8, 59), (9, 59), (14, 59)):
        if from_bcd(payload[index]) > maximum:
            raise ValueError("Invalid clock or timer value")
    if any(from_bcd(payload[i] & 127) > 23 for i in (4, 5)):
        raise ValueError("Invalid timer hour")
    # 60-86 F is exactly the 16-30 C range; wider values cannot be consistent.
    if payload[11] and not 60 <= from_bcd(payload[11]) <= 86:
        raise ValueError("Invalid Fahrenheit setpoint")
    return payload


def timer_time(payload: bytes, on: bool) -> time:
    """Read a stored schedule time, independently of its enable flag."""
    return time(
        from_bcd(payload[4 if on else 5] & 127), from_bcd(payload[8 if on else 9])
    )


def mutate_frame(template: bytes, clock: time, **changes) -> bytes:
    """Preserve unknown fields and change only requested, supported settings.

    Temperature is expressed in Celsius; temperature_f explicitly selects a
    Fahrenheit target without changing the remote display profile.
    Clock is refreshed with HA local time on every explicitly requested send.
    """
    parse_frame(template.hex())
    allowed = {
        "hvac_mode",
        "temperature",
        "temperature_f",
        "fan_mode",
        "preset",
        "display",
        "panel_lock",
        "timer_on",
        "timer_off",
        "on_time",
        "off_time",
    }
    if changes.keys() - allowed:
        raise ValueError("Unsupported command field")
    result = bytearray(template)
    if "hvac_mode" in changes:
        mode = changes["hvac_mode"]
        if mode not in (*MODES.values(), "off"):
            raise ValueError("Unsupported HVAC mode")
        if mode != "off":
            result[1] = (result[1] & 240) | next(
                k for k, v in MODES.items() if v == mode
            )
        result[10] = (result[10] & 240) | (12 if mode == "off" else 8)
        if mode in ("dry", "fan_only", "heat_cool"):
            result[7] &= ~2
        if mode == "dry":
            result[1] = 0x81
        elif mode in ("fan_only", "heat_cool") and result[1] >> 4 == 1:
            result[1] = (result[1] & 15) | 0x20
    mode = "off" if result[10] & 15 == 12 else MODES[result[1] & 15]
    if "temperature" in changes or "temperature_f" in changes:
        fahrenheit = "temperature_f" in changes
        if fahrenheit and ("temperature" in changes or not template[11]):
            raise ValueError("Fahrenheit target requires a Fahrenheit profile")
        value = changes["temperature_f" if fahrenheit else "temperature"]
        minimum, maximum = (60, 86) if fahrenheit else (16, 30)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not minimum <= value <= maximum
            or int(value) != value
        ):
            raise ValueError(f"Set an integer temperature from {minimum} to {maximum}")
        if mode == "fan_only":
            raise ValueError("Fan-only mode has no target temperature")
        if fahrenheit:
            result[11] = to_bcd(int(value))
            result[6] = to_bcd(math.floor((value - 32) * 5 / 9 + 0.5))
        else:
            result[6] = to_bcd(int(value))
            if template[11]:
                result[11] = to_bcd(math.ceil(value * 9 / 5 + 32))
    if "fan_mode" in changes:
        fan = changes["fan_mode"]
        if fan not in FANS.values():
            raise ValueError("Unsupported fan speed")
        if mode == "dry" and fan != "low":
            raise ValueError("Dry mode uses low fan")
        if mode in ("fan_only", "heat_cool") and fan == "auto":
            raise ValueError("Auto fan is available only in heating and cooling")
        result[1] = (result[1] & 15) | (
            next(k for k, v in FANS.items() if v == fan) << 4
        )
    if "preset" in changes:
        if changes["preset"] not in ("none", "sleep"):
            raise ValueError("Unsupported preset")
        if changes["preset"] == "sleep" and mode not in ("heat", "cool"):
            raise ValueError("Turn on heat or cool before enabling Sleep")
        result[7] = (result[7] & ~2) | (2 if changes["preset"] == "sleep" else 0)
    for name, index, mask, inverted in (
        ("display", 13, 64, True),
        ("panel_lock", 13, 128, False),
        ("timer_on", 4, 128, False),
        ("timer_off", 5, 128, False),
    ):
        if name in changes:
            enabled = changes[name]
            if type(enabled) is not bool:
                raise ValueError("A switch setting must be boolean")
            result[index] = (result[index] & ~mask) | (
                mask if enabled != inverted else 0
            )
    for name, hour_index, minute_index in (("on_time", 4, 8), ("off_time", 5, 9)):
        if name in changes:
            value = changes[name]
            if (
                not isinstance(value, time)
                or value.second
                or value.microsecond
                or value.tzinfo
            ):
                raise ValueError(
                    "Timer times must be local hours and minutes without seconds"
                )
            result[hour_index] = (result[hour_index] & 128) | to_bcd(value.hour)
            result[minute_index] = to_bcd(value.minute)
    result[2], result[3], result[14] = map(
        to_bcd, (clock.minute, clock.hour, clock.second)
    )
    for start in (0, 8):
        index = start + 7
        result[index] = (checksum(bytes(result[start : start + 8])) << 4) | (
            result[index] & 15
        )
    parse_frame(result.hex())
    return bytes(result)


def default_frame() -> bytes:
    """Starting settings used until a remote frame is received.

    This is a requested template, not an observation: off, heat/cool, 22 C, high
    fan (the remote's AUTO mode uses high, never auto fan), panel on/unlocked,
    sleep off, timer enables clear, unknown bits zero.
    """
    result = bytearray(
        [0x16, 0x2A, 0, 0, 0x09, 0x10, 0x22, 0, 0, 0, 0x0C, 0, 0, 0, 0, 0]
    )
    for start in (0, 8):
        result[start + 7] = checksum(bytes(result[start : start + 8])) << 4
    return parse_frame(result.hex())
