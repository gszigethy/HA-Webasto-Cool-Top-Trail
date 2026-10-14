# ESPHome files

For installation, start with the [step-by-step guide](../docs/installation.md). It explains what to paste into Device Builder, which pins to set, and how to connect the ESP32 to Home Assistant. No header file needs to be placed manually.

## Files for normal use

| File | Purpose |
| --- | --- |
| [bridge.example.yaml](bridge.example.yaml) | ESPHome configuration for sending AC commands and optionally receiving handheld remote commands |
| [packages/bridge.yaml](packages/bridge.yaml) | Shared sending action and transport configuration; downloaded automatically |
| [packages/receiver.yaml](packages/receiver.yaml) | Optional receiver configuration; downloaded automatically |
| [secrets.example.yaml](secrets.example.yaml) | Example secret names; replace placeholders with private values in your own `secrets.yaml` |

The example uses GPIO26 for the transmitter and GPIO32 for the receiver. **Change these to match your wiring.** For a transmitter-only setup, remove the `esp32/packages/receiver.yaml` line from the package list. The bridge package keeps the **Transmitted IR frame** sensor and sending action. Keep their names: the integration finds them by name.

ESPHome downloads the codec from [components/webasto_ir](../components/webasto_ir) automatically. The `webasto_ref` substitution chooses both the package and component revision. This support was added after beta 1; the current example uses `main`, and cannot use the beta 1 tag.

The Home Assistant integration provides the climate control. The ESPHome configuration provides the connection and infrared sender; it does not create a second climate entity.

## Files for protocol research

These are not needed for normal installation:

- [receiver.example.yaml](receiver.example.yaml): USB-only capture firmware used to record remote signals. It has no Home Assistant sending action.
- [baseline.yaml](baseline.yaml): the sanitized original caravan prototype, with its fixed commands and GPIO2 transmitter.
- [baseline-review.md](baseline-review.md): review of that prototype.

The separate debugging ESP used GPIO32 for receiving and GPIO26 for sending. It was identified as an ESP32-PICO-D4 with 4 MB flash. The old prototype's commented GPIO23 receiver was not verified wiring.

For research, see the [capture procedure](../docs/ir-capture.md) and [protocol documentation](../docs/ir-protocol.md). Retain third-party attribution and license terms when importing other implementations. Keep device backups, real Wi-Fi details, and API keys out of Git.
