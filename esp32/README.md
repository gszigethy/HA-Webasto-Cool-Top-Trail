# ESPHome device YAML

[example.yaml](example.yaml) is the only file you need. Paste it into ESPHome Device Builder; comments in the file say what to change (pins, board) and what to remove if you have no IR receiver.

ESPHome downloads the IR codec (`webasto_ir.h`) from [components/webasto_ir](../components/webasto_ir) through `external_components:`. You don't place any file manually.

Step-by-step instructions: [installation guide](../docs/installation.md).

The original prototype YAML and the capture firmware used to decode the remote are kept as research evidence in [captures/](../captures/).
