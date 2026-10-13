"""Analyze complete CARRIER_AC128 pulse arrays without contacting hardware.

This research decoder handles the 267-duration layout in the supplied corpus.
It accepts timing variation, checks both checksums, and preserves the 16 bytes.
It is not a streaming receiver or a production command encoder.
"""

import argparse
import json
from collections.abc import Sequence
from datetime import time
from pathlib import Path

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "captures/baseline/packets.json"

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


def construct_climate_payload(
    template: bytes,
    *,
    hvac_mode: str,
    target_temperature_c: int,
    clock: time,
) -> bytes:
    """Construct a complete packet for locally corroborated heat/cool/off modes.

    Preserve auxiliary, reserved, unit, and counter fields from a validated
    complete state. This research builder is not connected to any transmitter.
    Fahrenheit templates require additional temperature handling and are rejected.
    """
    validate_payload(template)
    if not template[7] & 0x08 or template[11] != 0:
        raise ValueError("Only the locally validated Celsius-only profile is supported")
    if hvac_mode not in ("heat", "cool", "off"):
        raise ValueError("Only heat, cool, and off have local baseline evidence")
    if type(target_temperature_c) is not int or not 16 <= target_temperature_c <= 30:
        raise ValueError("The baseline supports integer setpoints from 16 to 30 C")

    def bcd(value: int) -> int:
        return ((value // 10) << 4) | (value % 10)

    result = bytearray(template)
    if hvac_mode != "off":
        mode = 0x8 if hvac_mode == "heat" else 0x2
        result[1] = (result[1] & 0xF0) | mode
    result[10] = (result[10] & 0xF0) | (0x0C if hvac_mode == "off" else 0x08)
    result[6] = bcd(target_temperature_c)
    result[2], result[3], result[14] = map(
        bcd, (clock.minute, clock.hour, clock.second)
    )
    for start in (0, 8):
        index = start + 7
        result[index] = (checksum(bytes(result[start : start + 8])) << 4) | (
            result[index] & 0xF
        )
    return bytes(result)


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


def main() -> None:
    """Print reproducible analysis for the imported pulse corpus."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", nargs="?", type=Path, default=DEFAULT_CORPUS)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text())
    results = []
    for command in corpus["commands"]:
        result = interpret_payload(decode_pulses(command["pulses_us"]))
        results.append({"label": command["label"], **result})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
