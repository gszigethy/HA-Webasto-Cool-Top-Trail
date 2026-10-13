# HA Webasto Cool Top Trail

[![CI](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/ci.yml/badge.svg)](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/ci.yml)
[![Validate](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/validate.yml/badge.svg)](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A community Home Assistant custom integration for **Webasto Cool Top Trail**
motorhome and caravan air conditioners, made by **Houghton**.
The goal is to map verified air conditioner functionality to Home Assistant
entities, with installation through HACS and an ESP32 infrared bridge.

## Current status

**Development scaffold, version 0.0.1. No air conditioner control yet.**

Implemented:

- HACS custom-repository layout and integration metadata.
- Setup through Home Assistant's UI; multiple named scaffold entries.
- A diagnostic **Protocol status** sensor with state `awaiting_protocol`.
- Tests for configuration, device/entity registration, reload, and unload.
- GitHub Actions for lint, formatting, tests, hassfest, and HACS validation.

Pending:

- Review of the existing working prototype.
- ESP32 receiver captures, IR decoding, and model-specific capability validation.
- Bridge transport selection and, for control, IR transmitter support.
- Climate and auxiliary entities based on verified capabilities.

The status sensor describes integration development readiness. It does not
report connection health, actual AC operation, or captured remote settings.
The scaffold does not connect to hardware or send commands.

## Installation through HACS

Requires **Home Assistant 2026.10.1 or newer** and HACS.

1. In HACS, open **Custom repositories**.
2. Add `https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail` with type **Integration**.
3. Download **HA Webasto Cool Top Trail** and restart Home Assistant.
4. Open **Settings > Devices & services > Add integration**.
5. Search for **Webasto Cool Top Trail** and give the scaffold a name.

HACS can install from `main` while there are no releases. This project is not
listed in the HACS default catalog. Home Assistant Brands registration is also
pending; its check alone is explicitly skipped in the HACS validation workflow.

For manual installation, copy `custom_components/webasto_cool_top_trail` into
your Home Assistant `config/custom_components` directory, then restart and
follow steps 4-5.

## Protocol research and entity mapping

- [Proposed entity map](docs/entity-map.md)
- [IR capture procedure](docs/ir-capture.md)
- [Capture storage conventions](captures/README.md)
- [ESP32 development notes](esp32/README.md)
- [Hungarian Cool Top Trail 20/24 manual](https://varadicaravan.hu/wp-content/uploads/2022/04/Webasto-Cool-Top-Trail-20_24.pdf)

Only the 20/24 family is documented by the supplied manual. Other Houghton or
Webasto variants need their own evidence before being declared supported.

## Development

Use Python 3.14.2 or newer. Tests currently use Home Assistant 2026.10.1.

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for implementation and release conventions.

## License

[MIT](LICENSE). This community project is not affiliated with or endorsed by
Webasto or Houghton. External manuals remain the property of their owners and
are linked rather than redistributed.
