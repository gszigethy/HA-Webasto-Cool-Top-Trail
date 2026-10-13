# ESPHome transmitter and ESP32 receiver

An ESPHome IR transmitter is already deployed in the caravan and can emit basic
commands. This directory is reserved for its configuration, the existing working
prototype, and future receiver/bridge code once provided. Exact boards, pin
mappings, and the prototype's command implementation are still pending.

When importing the prototype, retain attribution, its original license, board
and library requirements, and the revision that generated each capture.
The repository's MIT license does not replace third-party license terms.

The planned receiver will support protocol research and observation of remote
commands. Enhance the existing transmitter to construct verified commands for
the full climate interface. Review its current ESPHome configuration before
choosing how the HACS integration invokes commands and receives state updates.

Keep secrets in local ESPHome `secrets.yaml`; do not commit credentials or the
caravan's private network settings. Use documented placeholders in shared YAML.
