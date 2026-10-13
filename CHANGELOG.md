# Changelog

## Unreleased - Protocol research

- Archive button-by-button MVP captures for all modes, fan settings, temperature,
  and C/F switching; correct the unconfirmed byte-7 unit-bit interpretation.

- Validate and archive the first live ON/OFF pair at cool/auto/22 C; confirm that
  OFF retains mode/fan/setpoint and uses a separate power flag.

- Archive sanitized user-provided ESPHome YAML and review its control behavior.
- Preserve 31 distinct IR arrays and identify their CARRIER_AC128 wire format.
- Document the byte map, timing variation, full-state construction, checksums,
  source revisions, and which features remain unverified on the Webasto unit.
- Add a timing-tolerant research decoder and capture-backed regression tests.
- Reconstruct all baseline payloads from complete state and nominal IR timing;
  add a serial raw-log collector with wrapped-line and malformed-frame tests.
- Add GPIO32 RX / GPIO26 TX capture firmware and ESPHome config validation CI.

## 0.0.1 - Development scaffold

- Initial HACS-compatible custom integration layout and UI setup.
- Protocol status diagnostic entity; setup, reload, unload, and multi-entry tests.
- CI for lint, formatting, Home Assistant tests, hassfest, and HACS validation.
- Houghton attribution and a proposed entity map linked to the Hungarian manual.
- ESP32 prototype and raw capture directories with research instructions.

IR decoding, ESP32 communication, and AC controls are not implemented.
