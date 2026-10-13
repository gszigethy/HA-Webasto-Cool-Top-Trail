# Proposed entity map

This is a design proposal, not a list of implemented entities. The initial
integration exposes only its protocol status diagnostic sensor. The intended
primary entity is `climate`, backed by the existing ESPHome IR transmitter.

## Climate interface

Plan for `async_set_hvac_mode`, `async_turn_on`, `async_turn_off`,
`async_set_temperature`, and verified fan/preset methods. Represent power-off as
HVAC mode `off` and remember the last non-off mode for turning on. Capabilities
will be model-specific. The existing basic transmitter commands are the starting
point; complete command construction and state tracking must be verified before
the climate entity is exposed.

Source: [Hungarian Cool Top Trail 20/24 manual](https://varadicaravan.hu/wp-content/uploads/2022/04/Webasto-Cool-Top-Trail-20_24.pdf),
printed pages 14-19, sections 5.5-5.17. The cover identifies Houghton as maker.

| Documented feature | Proposed Home Assistant mapping | Manual reference |
| --- | --- | --- |
| Power | Climate `off` / remembered mode | 5.6 |
| Cooling, heating, drying, ventilation, automatic heat/cool selection | Climate `cool`, `heat`, `dry`, `fan_only`, `heat_cool` | 5.9 |
| Target temperature, 16-30 °C; unavailable in ventilation | Climate target temperature | 5.7 |
| Low, medium, high, automatic fan; automatic limited to cooling/heating | Climate fan mode | 5.8 |
| Sleep; limited to cooling/heating | Climate preset `sleep` | 5.13 |
| Air-distributor display | Switch | 5.5 |
| Air-distributor touch-control lock | Switch | 5.5 |
| Timer enable modes and on/off times | Select plus time entities, if transmitted | 5.10-5.12 |
| Celsius/Fahrenheit display selection | Select, if transmitted | 5.14 |
| Manually adjusted outlet louvers | No IR swing entity | 5.17 |

The manual describes user functions, not frame encoding or feedback. Every
proposed mapping still needs captures. Exact model/remote variants must be
identified before choosing capability limits.

## State semantics

- A receiver observes remote transmissions. A captured setting does not prove
  that the appliance received it or reached that state.
- The existing ESPHome transmitter sends commands. The new receiver observes
  transmissions for decoding and possible remote-state synchronization.
- Separate requested settings, last observed remote settings, and any actual
  appliance feedback. Do not label a setpoint as measured room temperature.
- Do not report `hvac_action`, temperature telemetry, energy use, faults, or
  availability without a real source for each value.
- Capture tests must determine whether commands contain complete state,
  individual deltas, toggles, or different frame types.
- Do not assign known protocol names, checksums, timing tolerances, or firmware
  compatibility without checking them against the prototype and recordings.

## Implementation order

1. Archive the prototype with its license and provenance.
2. Identify the exact AC, remote, ESP32 board, and IR receiver.
3. Record repeatable captures and document frame boundaries and encoding.
4. Implement a pure decoder with capture-backed regression tests.
5. Review the existing ESPHome configuration and define its command/state interface.
6. Enhance its command encoder and map the verified controls into a climate entity.
7. Test on hardware before claiming supported models or publishing a usable release.
