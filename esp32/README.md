# ESPHome files

For installation, start with the [step-by-step guide](../docs/installation.md). It explains where to put the files, what to change for your board, and how to connect the ESP32 to Home Assistant.

## Files for normal use

| File | Purpose |
| --- | --- |
| [bridge.example.yaml](bridge.example.yaml) | ESPHome configuration for sending AC commands and optionally receiving handheld remote commands |
| [webasto_ir.h](webasto_ir.h) | Required companion code; put beside your device YAML without editing it |
| [secrets.example.yaml](secrets.example.yaml) | Example secret names; replace placeholders with private values in your own `secrets.yaml` |

The example uses GPIO26 for the transmitter and GPIO32 for the receiver. **Change these to match your wiring.** For a transmitter-only setup, remove the `remote_receiver:` section but keep both text sensors and the sending action.

The Home Assistant integration provides the climate control. The ESPHome configuration provides the connection and infrared sender; it does not create a second climate entity.

## Files for protocol research

These are not needed for normal installation:

- [receiver.example.yaml](receiver.example.yaml): USB-only capture firmware used to record remote signals. It has no Home Assistant sending action.
- [baseline.yaml](baseline.yaml): the sanitized original caravan prototype, with its fixed commands and GPIO2 transmitter.
- [baseline-review.md](baseline-review.md): review of that prototype.

The separate debugging ESP used GPIO32 for receiving and GPIO26 for sending. It was identified as an ESP32-PICO-D4 with 4 MB flash. The old prototype's commented GPIO23 receiver was not verified wiring.

For research, see the [capture procedure](../docs/ir-capture.md) and [protocol documentation](../docs/ir-protocol.md). Retain third-party attribution and license terms when importing other implementations. Keep device backups, real Wi-Fi details, and API keys out of Git.
