# Changelog

## 1.0.0 beta 1 — 2026-10-14

First public prerelease for Houghton-made Webasto Cool Top Trail air conditioners.

- HACS installation and setup by selecting an existing ESPHome bridge device.
- One climate entity for on/off, cool, heat, dry, fan-only, automatic heat/cool,
  target temperature, fan speed and Sleep.
- Native Celsius and Fahrenheit targets, with capture-backed conversion rules.
- Panel display and control lock switches, independent ON/OFF timer switches,
  and schedule time entities. Every explicit command refreshes the appliance clock.
- Full-state CARRIER_AC128 encoding and decoding with integrity checks,
  timing-tolerant reception, and preservation of unknown fields.
- ESPHome receiver/transmitter bridge, transmitter-only defaults, and no API
  reboot timeout when Home Assistant is disconnected.
- State persistence, connection diagnostics, serialized commands, and bounded
  failure handling without automatic retransmission.
- User installation guide, entity reference, functional/technical designs, and
  documented protocol research with sanitized remote captures.
- CI for lint/format, 288 tests, a 90% coverage gate, Sonar with real coverage,
  ESPHome validation and firmware compile, Hassfest, and HACS. Verified integration
  statement coverage: 99.27%.
- Upgrade checkout to v7.0.1 and setup-python to v7.0.0; handle Sonar secret
  restrictions on Dependabot-triggered workflows.

Requires Home Assistant 2026.10.1 or newer and ESPHome 2026.9.1 or newer.
IR state is assumed: neither transmission nor reception proves appliance operation.
Physical acceptance of generated commands by an actual AC remains unverified.

## Development history

Before this prerelease, the repository used 0.0.1 scaffold and 0.1.0 development
versions. These were not published releases. Development progressed from the
original 31-command ESPHome prototype through button-by-button remote captures,
full-state protocol decoding, Home Assistant entity implementation, and
Fahrenheit control. Research evidence remains in `captures/` and `docs/`.
