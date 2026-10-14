"""Compile the deployed C++ codec and replay every archived raw waveform."""

import json
import subprocess
from pathlib import Path

from custom_components.webasto_cool_top_trail.protocol import (
    decode_pulses,
    encode_pulses,
)

ROOT = Path(__file__).resolve().parents[1]


def test_firmware_codec_against_archived_waveforms(tmp_path):
    source = tmp_path / "codec.cpp"
    source.write_text(r"""
#include "webasto_ir.h"
#include <iostream>
#include <sstream>
int main() {
  std::string line;
  while (std::getline(std::cin, line)) {
    webasto_ir::Frame frame;
    bool ok;
    if (line.rfind("HEX|", 0) == 0) {
      ok = webasto_ir::parse(line.substr(4), frame);
    } else {
      std::vector<int32_t> raw;
      std::stringstream in(line);
      std::string value;
      while (std::getline(in, value, ',')) raw.push_back(std::stol(value));
      ok = webasto_ir::decode(raw, frame);
    }
    if (!ok) { std::cout << "INVALID\n"; continue; }
    std::cout << webasto_ir::format(frame) << '|';
    auto encoded = webasto_ir::encode(frame);
    for (size_t i = 0; i < encoded.size(); ++i) {
      if (i) std::cout << ',';
      std::cout << encoded[i];
    }
    std::cout << '\n';
  }
}
""")
    binary = tmp_path / "codec"
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=undefined",
            "-I",
            str(ROOT / "components" / "webasto_ir"),
            str(source),
            "-o",
            str(binary),
        ],
        check=True,
        capture_output=True,
    )

    def walk(value):
        if isinstance(value, dict):
            if "pulses_us" in value:
                yield value["pulses_us"]
            for key, child in value.items():
                if key != "pulses_us":
                    yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    pulses = []
    for path in (ROOT / "captures").glob("**/packets.json"):
        pulses.extend(walk(json.loads(path.read_text())))
    pulses += [[-2147483648], [0] * 267, [340] * 267]
    expected = []
    for raw in pulses:
        try:
            frame = decode_pulses(raw)
            expected.append(
                frame.hex(" ").upper() + "|" + ",".join(map(str, encode_pulses(frame)))
            )
        except ValueError:
            expected.append("INVALID")
    inputs = [",".join(map(str, raw)) for raw in pulses]
    valid = decode_pulses(pulses[0]).hex(" ").upper()
    inputs += [
        "HEX|" + valid,
        "HEX|16",
        "HEX|" + valid + " FF",
        "HEX|GG",
        "HEX|" + valid[:-1] + "F",
    ]
    expected += [expected[0], "INVALID", "INVALID", "INVALID", "INVALID"]
    result = subprocess.run(
        [str(binary)],
        input="\n".join(inputs) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.splitlines() == expected
    assert not result.stderr
