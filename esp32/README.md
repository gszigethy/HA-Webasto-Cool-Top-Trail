# ESPHome transmitter and ESP32 receiver

An ESPHome IR transmitter is already deployed in the caravan and emits basic
commands. The user supplied its YAML on 2026-10-13; see the sanitized
[baseline](baseline.yaml) and [behavior review](baseline-review.md). Its existing
IR TX is GPIO2 and the original commented receiver example was GPIO23.

For the separately attached capture ESP, the user specified **GPIO32 RX / GPIO26
TX**. Chip inspection identified ESP32-PICO-D4 with 4MB flash. The
[capture firmware](receiver.example.yaml) uses these pins, raw DEBUG logging,
and USB serial only. Its transmitter has no send actions. Host addresses and
device-specific identifiers are deliberately kept out of shared configuration.

When importing the prototype, retain attribution, its original license, board
and library requirements, and the revision that generated each capture.
The repository's MIT license does not replace third-party license terms.

The receiver will support protocol research and observation of remote commands.
The baseline matches the existing `CARRIER_AC128` wire format; see the
[protocol document](../docs/ir-protocol.md). Enhance the transmitter to construct
verified complete-state commands for the full climate interface.

Keep secrets in local ESPHome `secrets.yaml`; do not commit credentials or the
caravan's private network settings. Use documented placeholders in shared YAML.

## Implemented full-frame bridge

[bridge.example.yaml](bridge.example.yaml) and [webasto_ir.h](webasto_ir.h) now
provide the production transport for the HACS integration. The firmware exposes
Received IR frame and Transmitted IR frame diagnostics plus a validated native
send_frame action with a success/error response. HA owns climate and auxiliaries;
there is no competing native ESPHome climate entity. See the
[installation guide](../docs/installation.md) for merging into the caravan ESP,
transmitter-only use, pins, secrets and pairing. The bridge was compiled locally
but has not been flashed by repository implementation work. The capture-only
firmware remains a separate research tool.
