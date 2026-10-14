# ESPHome files

For installation, start with the [step-by-step guide](../docs/installation.md). It explains what to paste into Device Builder, which pins to set, and how to connect the ESP32 to Home Assistant. No header file needs to be placed manually.

## Files for normal use

| File | Purpose |
| --- | --- |
| [bridge.example.yaml](bridge.example.yaml) | ESPHome configuration for sending AC commands and optionally receiving handheld remote commands |
| [secrets.example.yaml](secrets.example.yaml) | Example secret names; replace placeholders with private values in your own `secrets.yaml` |

The example uses GPIO26 for the transmitter and GPIO32 for the receiver. **Change these to match your wiring.** For a transmitter-only setup, delete the two parts marked *Only with an IR receiver*. Keep the `send_frame` action and sensor names: the integration finds them by name.

ESPHome downloads the codec from [components/webasto_ir](../components/webasto_ir) automatically. It only provides the codec header; the sending action, sensors and IR hardware are all in the single example YAML. The component was added after beta 1, so the example uses `main`.

The Home Assistant integration provides the climate control. The ESPHome configuration provides the connection and infrared sender; it does not create a second climate entity.

## Files for protocol research

These are not needed for normal installation:

- [receiver.example.yaml](receiver.example.yaml): USB-only capture firmware used to record remote signals. It has no Home Assistant sending action.
- [baseline.yaml](baseline.yaml): the sanitized original caravan prototype, with its fixed commands and GPIO2 transmitter.
- [baseline-review.md](baseline-review.md): review of that prototype.

The separate debugging ESP used GPIO32 for receiving and GPIO26 for sending. It was identified as an ESP32-PICO-D4 with 4 MB flash. The old prototype's commented GPIO23 receiver was not verified wiring.

For research, see the [capture procedure](../docs/ir-capture.md) and [protocol documentation](../docs/ir-protocol.md). Retain third-party attribution and license terms when importing other implementations. Keep device backups, real Wi-Fi details, and API keys out of Git.
