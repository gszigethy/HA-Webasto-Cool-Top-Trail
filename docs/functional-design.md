# Functional design (FD)

## Purpose and scope

Control Houghton-made Webasto Cool Top Trail caravan/motorhome ACs from Home
Assistant through ESPHome infrared hardware. Replace the prototype's fixed
recordings with complete state construction. The local remote-capture corpus
identifies CARRIER_AC128, verifies its framing/checksums, and corroborates all
five operating modes, four fan codes, power, temperature, panel flags, Sleep,
clock and timer fields. The supplied manual is for 20/24; exact installed model
and physical synthesized-command acceptance remain unverified.

Provide HACS-installable HA configuration through the UI. Keep hardware secrets
and Wi-Fi/API transport with built-in ESPHome. Run entirely locally. No vendor
cloud, broker, HTTP server, background command replay or HA YAML helpers.

## Users and workflows

**Installer:** merge the bridge transport/header into ESPHome, choose actual
hardware pins and secrets, compile/flash when ready, pair built-in ESPHome,
install HACS integration, select receiver sensor/send action. Learning a valid
remote frame initializes requested settings. A transmitter-only installer can
explicitly choose the documented default starting profile instead.

**Occupant:** use one climate entity to turn the AC off/on, choose heat/cool/dry/
fan-only/automatic heat-cool selection, set temperature, fan and Sleep. Configure
panel display/control lock and recurring ON/OFF schedules on the same device.
Use physical remote normally when a receiver is installed; full-state frames
update all HA settings together. There is no separate power/fan helper to drift
out of sync with climate.

**Maintainer:** use protocol status and frame endpoints for diagnosis. Raw
capture-only firmware and labelled archives support further reverse engineering.
Receiver captures document transmitted intent; actual appliance responses need
observation during acceptance testing.

## Requirements and delivered behavior

| Requirement | Implemented behavior |
| --- | --- |
| Power and remembered mode | Climate off flag; turn on resumes stored mode; target edits while off keep off |
| Native climate model | Built-in HVAC enums; single target; fan modes; Sleep preset |
| Mode-specific controls | Dry low fan; fan-only has no target; auto fan restricted to heat/cool; Sleep heat/cool only |
| Auxiliaries | Panel display/lock and timer enable switches; separate local time entities |
| Full-state transmission | Mutate latest validated frame, preserve untouched/unknown fields, refresh clock, recalculate checksums |
| Remote synchronization | Valid received frame updates all settings; noise and malformed/unsupported state ignored |
| Reliable state bookkeeping | Serialize commands; report local action errors; failed sends don't advance commanded state; newer received command wins a concurrent send |
| Recovery | Retain frame over reload/restart without replay; connectivity determines control availability |
| Multiple units | Independent config entries, devices, identities, storage and per-entry command serialization |
| Optional measured temperature | Existing °C/°F sensor only; absent/invalid measurement stays unknown |
| Privacy | Secrets remain in ESPHome/local files; archives exclude host/device credentials |
| Documentation | Protocol/evidence, setup, entities, FD/TD and explicit acceptance checklist |

## Entity decisions

Climate owns HVAC, target, fan and Sleep because HA has standard fields for them.
Panel display and control lock are boolean configuration switches. The latter
locks appliance touch controls and is not a security/door lock. Independent ON
and OFF enables are two switches, representing all four combinations without
a redundant selector. Schedule times use HA time entities with HH:MM precision.
An explicit clock-sync button represents a momentary action. Protocol status
is a diagnostic enum sensor. See [the full reference](entity-map.md).

No separate Sleep switch duplicates the climate preset. No fake measured room
temperature comes from target temperature. No compressor action, power/energy,
fault, remote battery, swing or unvalidated ECO control is exposed. Unit choice
in the HA interface uses HA's unit system; the remote's display-unit encoding is
not sufficiently understood for a writable C/F selector.

## State and availability contract

All climate/control settings describe **assumed requested state**. A local
ESPHome confirmation means its action handled transmission; a receiver frame
means a remote or local transmitter emitted a command. Neither proves the AC
received it, is heating/cooling, or has reached a temperature. Timers may run
without generating any IR, so HA cannot observe those transitions.

With learning enabled and no template, controls are unavailable. With an
explicit default profile they start with assumed off/cool/24 °C/auto, auxiliaries
at documented defaults, without emission. A saved frame restores the last
requested state; a stale replay of the old receiver value does not undo it.
A new valid received frame replaces it. Disconnects make controls unavailable
and retain settings; reconnects do not send commands. Protocol status remains
readable. Native send failure leaves state unchanged, though timeout outcome is
ambiguous: a command could already have been emitted, and no retry is automatic.

Temperature is rounded to the nearest 1 °C after HA converts its display units.
Captured Fahrenheit profiles remain usable for other controls, but target edits
require learning a Celsius profile. This avoids inventing the observed 24 °C /
76 °F mapping. Mode changes keep one current setpoint; they do not reproduce the
remote's per-mode memory. Switching to dry/fan-only/heat_cool clears incompatible
Sleep; turning off retains it and the other auxiliary flags.

## Timer behavior

Schedule times are local wall-clock times stored independently of their enables.
Changing time leaves its enable unchanged. Disabling leaves the stored time
unchanged. Both timers can be enabled. Every explicit HA send refreshes the
appliance clock; there is no autonomous schedule runner or periodic clock send.
The combined ON/OFF mode is described as daily recurring by manual §5.12.
Standalone ON/OFF execution details must be verified on the appliance.

The physical TIMER selector cycles ON → OFF → both → neither while blinking.
After ten seconds the remote returns to clock display with any enabled ON/OFF
icons still showing. SET TIME selects clock/ON/OFF time editing, and HOUR/MIN
selects the part to edit; these UI buttons need no corresponding HA entity.
Value edits produced full-state IR packets. Their precise transmit trigger
(arrow press or completion) is not yet isolated.

## Completion and acceptance boundaries

The repo implementation is complete for the documented Celsius control profile
and locally confirmed auxiliary fields. Static/isolated tests and firmware
builds validate software behavior. [Appliance acceptance](validation.md) is a
separate deployment step: no live HA configuration or firmware deployment is
performed by development. Broader model support, Fahrenheit setpoint writing,
unknown flag/counter interpretation and actual appliance telemetry are future
work requiring new evidence.
