"""Analyze complete CARRIER_AC128 pulse arrays without contacting hardware.

This research decoder handles the 267-duration layout in the supplied corpus.
It accepts timing variation, checks both checksums, and preserves the 16 bytes.
It is not a streaming receiver or a production command encoder.
"""

import argparse
import json
import sys
from datetime import time
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
# Import the pure codec directly without running the Home Assistant package setup.
sys.path.insert(0, str(REPOSITORY_ROOT / "custom_components/webasto_cool_top_trail"))

from protocol import (  # noqa: E402
    checksum,
    decode_pulses,
    encode_pulses,  # noqa: F401  # re-exported for tests and research use
    from_bcd,  # noqa: F401
    to_bcd,
    validate_payload,
)
from protocol import interpret_payload as interpret_protocol_payload  # noqa: E402

DEFAULT_CORPUS = REPOSITORY_ROOT / "captures/baseline/packets.json"


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

    result = bytearray(template)
    if hvac_mode != "off":
        mode = 0x8 if hvac_mode == "heat" else 0x2
        result[1] = (result[1] & 0xF0) | mode
    result[10] = (result[10] & 0xF0) | (0x0C if hvac_mode == "off" else 0x08)
    result[6] = to_bcd(target_temperature_c)
    result[2], result[3], result[14] = map(
        to_bcd, (clock.minute, clock.hour, clock.second)
    )
    for start in (0, 8):
        index = start + 7
        result[index] = (checksum(bytes(result[start : start + 8])) << 4) | (
            result[index] & 0xF
        )
    return bytes(result)


def interpret_payload(payload: bytes) -> dict:
    """Keep the baseline report's original Celsius-only field set."""
    state = interpret_protocol_payload(payload)
    for key in ("target_temperature_f", "remote_temperature_unit"):
        state.pop(key)
    return state


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
