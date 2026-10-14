# Webasto Cool Top Trail for Home Assistant

Control a **Webasto Cool Top Trail** caravan or motorhome air conditioner from Home Assistant, the same way the handheld remote does.

> **Status: beta.** The remote's infrared signals are fully decoded and the software is tested. Commands sent by this integration still need to be confirmed on the air conditioner itself. Please [report](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/issues) what works and what doesn't.

## How it works

```text
Home Assistant  ──Wi-Fi──▶  ESP32  ──infrared──▶  air conditioner
                              ▲
             handheld remote ─┘ (optional IR receiver)
```

- An **ESP32** with an **infrared (IR) LED** acts as the remote control. You set it up with ESPHome.
- This **integration** (installed with HACS) adds the air-conditioner controls to Home Assistant and tells the ESP32 what to send.
- An optional **IR receiver** on the ESP32 lets Home Assistant follow presses on the handheld remote.

Everything runs locally: no cloud and no account. There is no pairing and no button learning.

## What you get

| Control | What it does |
| --- | --- |
| Climate | Off, cool, heat, auto (heat/cool), dry, fan only; temperature in °C or °F; fan speed; Sleep |
| Panel display, Panel control lock | Switch the AC's display off, lock its buttons |
| On timer, Off timer, On time, Off time | The AC's own daily timers |
| Protocol status | Shows whether the ESP32 is connected and ready |

Infrared only goes one way. The AC never reports back, so Home Assistant shows the settings it last sent, not confirmed AC status.

## What you need

- **Home Assistant** 2026.10.1 or newer, with **[HACS](https://hacs.xyz/)**.
- **ESPHome** 2026.9.1 or newer, for example the ESPHome Device Builder add-on in Home Assistant.
- An **ESP32** board with an **IR transmitter LED** pointed at the AC.
- Optional: an **IR receiver** on the same ESP32.
- The GPIO pin numbers your transmitter (and receiver) are connected to.

## Installation

### Step 1: Set up the ESP32

1. In **ESPHome Device Builder**, create a new device and open its YAML editor.
2. Copy the API encryption key from the generated YAML (`api: encryption: key:`) and keep it for step 4.
3. Replace the whole YAML with the template below. It is also on GitHub: **[esp32/bridge.example.yaml](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/blob/main/esp32/bridge.example.yaml)**.
4. Open **Secrets** (top right in Device Builder) and add your Wi-Fi details and the key from point 2:

   ```yaml
   caravan_wifi_ssid: "YOUR_WIFI_NAME"
   caravan_wifi_password: "YOUR_WIFI_PASSWORD"
   api_encryption_key: "THE_KEY_FROM_POINT_2"
   ```

5. Edit the top of the template to match your hardware (see below), then click **Install**. The first install usually needs a USB cable; later updates work over Wi-Fi.

```yaml
# ESPHome bridge for the Webasto Cool Top Trail Home Assistant integration.
# Paste into ESPHome Device Builder, then set the pins and board for your hardware.
# Without an IR receiver, delete the two parts marked "Only with an IR receiver".
substitutions:
  device_name: webasto-ir-bridge
  friendly_name: Webasto IR Bridge
  transmitter_pin: GPIO26
  receiver_pin: GPIO32

esphome:
  name: ${device_name}
  friendly_name: ${friendly_name}
  min_version: 2026.9.1

esp32:
  board: esp32dev
  framework:
    type: esp-idf

# Downloads only the IR codec (webasto_ir.h); everything else is in this file.
external_components:
  - source: github://gszigethy/HA-Webasto-Cool-Top-Trail@main
    components: [webasto_ir]

webasto_ir:

wifi:
  ssid: !secret caravan_wifi_ssid
  password: !secret caravan_wifi_password

logger:
  level: INFO

ota:
  - platform: esphome

api:
  encryption:
    key: !secret api_encryption_key
  # Keep running when Home Assistant is out of reach (e.g. while travelling).
  reboot_timeout: 0s
  actions:
    # Keep this name: the integration looks for <device_name>_send_frame.
    - action: send_frame
      variables:
        frame: string
      then:
        - if:
            condition:
              lambda: |-
                webasto_ir::Frame bytes;
                return webasto_ir::parse(frame, bytes);
            then:
              - lambda: |-
                  webasto_ir::Frame bytes;
                  webasto_ir::parse(frame, bytes);
                  auto call = id(transmitter_ir).transmit();
                  call.get_data()->set_data(webasto_ir::encode(bytes));
                  call.get_data()->set_carrier_frequency(38000);
                  call.perform();
              # Longest frame is 251ms; acknowledge after the RMT completion callback.
              - delay: 300ms
              - if:
                  condition:
                    lambda: |-
                      return !id(transmitter_ir).is_failed() &&
                             !id(transmitter_ir).status_has_warning();
                  then:
                    - lambda: |-
                        webasto_ir::Frame bytes;
                        webasto_ir::parse(frame, bytes);
                        id(transmitted_frame).publish_state(webasto_ir::format(bytes));
              - api.respond:
                  success: !lambda |-
                    return !id(transmitter_ir).is_failed() &&
                           !id(transmitter_ir).status_has_warning();
                  error_message: "IR transmitter reported an error"
            else:
              - api.respond:
                  success: false
                  error_message: "Invalid CARRIER_AC128 frame"

remote_transmitter:
  id: transmitter_ir
  pin: ${transmitter_pin}
  carrier_duty_percent: 50%
  non_blocking: true

# Keep these names: the integration finds the sensors by name.
text_sensor:
  - platform: template
    id: transmitted_frame
    name: Transmitted IR frame
    entity_category: diagnostic
    update_interval: never
  # --- Only with an IR receiver ---
  - platform: template
    id: received_frame
    name: Received IR frame
    entity_category: diagnostic
    update_interval: never

# --- Only with an IR receiver ---
remote_receiver:
  id: receiver_ir
  pin:
    number: ${receiver_pin}
    inverted: true
  idle: 30ms
  buffer_size: 64kb
  filter: 50us
  tolerance: 25%
  on_raw:
    then:
      - lambda: |-
          webasto_ir::Frame bytes;
          if (webasto_ir::decode(x, bytes))
            id(received_frame).publish_state(webasto_ir::format(bytes));
```

**What to change:**

| Setting | Change it to |
| --- | --- |
| `transmitter_pin` | The GPIO your IR LED is connected to |
| `receiver_pin` | The GPIO your IR receiver is connected to |
| `board` | Your ESP32 board, for example `m5stack-atom` |
| `device_name`, `friendly_name` | Optional: the device's network name and display name |

**No IR receiver?** Delete the two parts marked *Only with an IR receiver*: the **Received IR frame** sensor and the `remote_receiver:` section.

You don't need to download any other file. When you install, ESPHome fetches the IR codec (`webasto_ir.h`) from this repository through `external_components:`; everything else is in this one YAML. Keep the `send_frame` action name and the *IR frame* sensor names: the integration finds them by name.

### Step 2: Add the ESP32 to Home Assistant

Go to **Settings → Devices & services**. The ESP32 usually appears as a discovered **ESPHome** device; click **Add**. If it doesn't, choose **Add integration → ESPHome** and enter its IP address. Use the encryption key from step 1 if asked.

### Step 3: Install this integration

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail` with type **Integration**.
3. Search for **Webasto Cool Top Trail** in HACS, download it, and **restart Home Assistant**.

### Step 4: Add the air conditioner

Go to **Settings → Devices & services → Add integration → Webasto Cool Top Trail** and fill in:

- **Name:** for example "Caravan AC".
- **ESPHome IR bridge:** the ESP32 from step 2.
- **Room temperature sensor:** optional, only used to show the current temperature.

### Step 5: First use

- **With a receiver:** point the handheld remote at the receiver and press any button once. Home Assistant takes over the remote's settings and the controls become available.
- **Without a receiver:** the controls are available right away. They start from default settings: off, cool, 24 °C, auto fan. Nothing is sent until you use a control.

Now try turning the AC on from Home Assistant and check that the AC responds.

## Good to know

- Every command sends **all** the AC's settings at once and sets the AC's clock. If someone uses the handheld remote and Home Assistant doesn't hear it, the next command from Home Assistant overwrites that change.
- Home Assistant doesn't see the AC's own timers switching it on or off.
- The ESP32 keeps working when Home Assistant is unreachable; it simply waits for the next command.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Setup says the device has no `send_frame` action | The ESP32 is online and was installed with the template above |
| Controls are unavailable / **Bridge disconnected** | The ESP32's power and Wi-Fi |
| Status says **Awaiting remote frame** | Press a button on the handheld remote, pointed at the receiver |
| Home Assistant changes but the AC doesn't | The transmitter pin, wiring, and that the IR LED points at the AC |

More help: [installation guide](docs/installation.md#if-something-does-not-work).

## More information

- [Detailed installation and everyday use](docs/installation.md)
- [Entities and automation examples](docs/entity-map.md)
- [ESPHome files explained](esp32/README.md)
- [How the IR protocol was decoded](docs/ir-protocol.md)
- [Testing status](docs/validation.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)
- [Manufacturer's manual (Hungarian)](https://varadicaravan.hu/wp-content/uploads/2022/04/Webasto-Cool-Top-Trail-20_24.pdf)
