# Home Assistant entity reference

These entities are implemented in version 0.1.0. Example IDs assume entry name
**Caravan AC** and no naming collisions; actual IDs come from the entity registry.
All eight entities share one Webasto Cool Top Trail device. IDs/unique IDs survive
reloads and entry-title changes; creating another entry gives it independent identity.

| Example entity ID | Domain / category | Behavior |
| --- | --- | --- |
| `climate.caravan_ac` | Climate / primary | Power, HVAC, target, fan, Sleep |
| `switch.caravan_ac_panel_display` | Switch / configuration | On shows panel display; off hides it |
| `switch.caravan_ac_panel_control_lock` | Switch / configuration | On locks panel touch controls; off unlocks |
| `switch.caravan_ac_on_timer` | Switch / configuration | Enable ON schedule |
| `switch.caravan_ac_off_timer` | Switch / configuration | Enable OFF schedule |
| `time.caravan_ac_on_time` | Time / configuration | Local ON time HH:MM |
| `time.caravan_ac_off_time` | Time / configuration | Local OFF time HH:MM |
| `sensor.caravan_ac_protocol_status` | Enum sensor / diagnostic | `awaiting_frame`, `ready`, `disconnected` |

The ESPHome device additionally exposes a Transmitted IR frame diagnostic
sensor and, with a receiver, a Received IR frame sensor. Those are transport endpoints, not duplicate climate
entities. Transmitted IR frame indicates local transmitter processing, not AC
acknowledgment. No separate power switch or fan entity duplicates climate controls.

## Climate semantics

| Control | Values / rules |
| --- | --- |
| HVAC | `off`, `cool`, `heat`, `dry`, `fan_only`, `heat_cool` |
| Remote AUTO | HA `heat_cool`, automatic heat/cool selection with one target; not HA's schedule/AI `auto` |
| Target | 16–30 °C or 60–86 °F, native 1-degree step; rounded to nearest integer after HA display-unit conversion |
| Fan | `auto`, `low`, `medium`, `high` in heat/cool; low only in dry; low/medium/high in fan-only or heat_cool; a received frame outside these rules (e.g. fan-only with auto) is shown as received |
| Sleep | Standard `sleep`/`none` climate preset; enabling requires active heat/cool |
| Turn off/on | Power flag changed; stored operating mode retained/resumed |
| Temperature while off | Updates the retained target and leaves power off |
| Mode change | Keeps current target; dry selects low fan; fan-only/heat_cool replace auto fan with high; modes incompatible with Sleep clear it |
| Current temperature | Optional selected external sensor, converted to °C; unknown for absent, unavailable, nonnumeric, nonfinite or wrong-unit sensor |
| HVAC action | Omitted: compressor activity cannot be inferred from a command |

Turning off retains Sleep and other auxiliaries. A user-requested incompatible
mode transition clears Sleep. The software retains the current target when
changing modes; it does not reproduce the physical remote's separate per-mode
setpoint memories. Physical-remote mode changes supply their own full target.
Fan-only target is hidden while its stored value is preserved in the packet.
Unsupported modes, fans, presets and timer seconds are rejected before transmit.

Fahrenheit-profile frames are decoded and preserved for power/fan/mode/auxiliary
changes, including target edits in native 1 °F steps (60–86 °F).
Celsius profiles use 1 °C steps (16–30 °C). HA converts its preferred display units. There is no C/F selector,
ECO preset, swing control, remote battery sensor, energy sensor, or fault sensor.
Lock is a configuration switch for panel controls, rather than a door/security
lock entity. Timer enables are independent boolean settings, avoiding a select
that duplicates ON/OFF/both combinations. Sleep uses the standard climate preset.

Sources: [HA climate entity guidelines](https://developers.home-assistant.io/docs/core/entity/climate/),
[HA time entity](https://developers.home-assistant.io/docs/core/entity/time/),
[manufacturer manual §§5.5–5.17](https://varadicaravan.hu/wp-content/uploads/2022/04/Webasto-Cool-Top-Trail-20_24.pdf)
and local labelled captures. These source mappings do not assert appliance tests.

## Service examples

These are examples to run after installation; repository development does not
execute them against a live installation.

```yaml
action: climate.set_temperature
target:
  entity_id: climate.caravan_ac
data:
  hvac_mode: cool
  temperature: 22
```

```yaml
action: climate.set_fan_mode
target:
  entity_id: climate.caravan_ac
data:
  fan_mode: low
```

```yaml
action: climate.set_preset_mode
target:
  entity_id: climate.caravan_ac
data:
  preset_mode: sleep
```

Set a schedule time first, then enable it:

```yaml
sequence:
  - action: time.set_value
    target:
      entity_id: time.caravan_ac_on_time
    data:
      time: "09:00:00"
  - action: switch.turn_on
    target:
      entity_id: switch.caravan_ac_on_timer
```

Both timer switches can be on. Timer events execute on the appliance and do not
produce HA feedback. Display and panel lock do not change climate power. All
controls send complete state, so unknown and untouched fields remain intact.
Every command HA sends refreshes the appliance clock from HA local time; there
is no separate clock-sync action.

Protocol status is always readable, including while other entities are unavailable.
`ready` describes software transport readiness. Control state is **assumed** and
may diverge from the appliance if IR is missed, another remote changes it outside
receiver range, or a timer executes. `state_source` identifies the software state
source; IR provides no appliance feedback. Repeated stale sensor values do not
overwrite newer saved commanded state on restart.
