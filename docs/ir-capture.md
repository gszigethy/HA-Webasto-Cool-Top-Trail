# IR capture procedure

An ESPHome IR transmitter already exists in the caravan and emits basic
commands. Its supplied YAML is archived in `esp32/baseline.yaml`. The capture
ESP uses user-specified GPIO32 RX and GPIO26 TX and identifies as ESP32-PICO-D4
with 4MB flash. Use `esp32/receiver.example.yaml` for capture-only firmware.
Record original output even if a library already reports a decoded value;
carrier frequency remains a configured value rather than a measured one.

## Record the environment

For each capture session, record:

- Exact AC model and label identifiers that distinguish hardware variants.
- Remote model and a description of its buttons/display.
- ESP32 board, receiver part number, GPIO, supply voltage, and wiring.
- Firmware/source commit and library versions.
- Receiver polarity, timestamp source, and timing units.
- Remote starting settings, action performed, and resulting displayed settings.

Avoid publishing Wi-Fi credentials, network identifiers, or unrelated device
serial numbers. Capture only relevant prototype/source and IR data.

## Capture one change at a time

1. Start from a documented remote state.
2. Capture an identical command several times without changing settings.
3. Change one setting and capture several repetitions.
4. Return to the baseline and repeat to detect hidden counters or toggle bits.
5. Record power on/off, every mode, temperature steps and endpoints, fan speeds,
   sleep, display, lock, and timer actions supported by the remote.
6. Also record buttons that produce no transmission, held buttons, repeats,
   remote reset, and commands after a battery change where practical.

Initial analysis should use the receiver only. Hardware command transmission
comes after frame structure and command semantics have been established.

## Preserve raw evidence

Use an isolated session directory under `captures/`, for example
`captures/<model>/<session-id>/`. Keep raw text logs or JSON in the format
produced by the actual firmware. Add a `session.json` with the environment above
and a table in `README.md` relating each file to the button press and before/after
state. Do not add invented pulse arrays as if they were real recordings.

Preserve mark/space polarity, units, inter-frame gaps, and repeats. If a receiver
only provides demodulated timings, document that carrier frequency was not
measured. Keep normalized decoder fixtures separate from the raw captures and
link each fixture to its source.

## What the first analysis should establish

- Frame and repeat boundaries, bit order, and timing distributions.
- Constant, changing, state, counter, and integrity-check fields.
- Whether settings are transmitted as a full state or separate commands.
- Which remote-only functions actually appear in IR.
- How reliably an observed command can reconstruct state after missed frames.
