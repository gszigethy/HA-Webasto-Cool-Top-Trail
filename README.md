<!-- ha-marketplace:exclude-start -->
<p align="center">
  <img width="120" src="custom_components/webasto_cool_top_trail/brand/icon@2x.png" alt="Webasto Cool Top Trail icon">
</p>
<!-- ha-marketplace:exclude-end -->

<h1 align="center">Webasto Cool Top Trail for Home Assistant</h1>

<!-- ha-marketplace:exclude-start -->
<p align="center">
  <a href="https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/validate.yml"><img alt="Validate" src="https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/actions/workflows/validate.yml/badge.svg"></a>
  <a href="https://sonarcloud.io/summary/new_code?id=gszigethy_HA-Webasto-Cool-Top-Trail"><img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=gszigethy_HA-Webasto-Cool-Top-Trail&metric=alert_status"></a>
  <a href="https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/gszigethy/HA-Webasto-Cool-Top-Trail"></a>
  <a href="https://hacs.xyz"><img alt="HACS Default" src="https://img.shields.io/badge/HACS-Default-41BDF5.svg"></a>
  <a href="https://www.home-assistant.io"><img alt="Home Assistant 2026.10.1+" src="https://img.shields.io/badge/Home%20Assistant-2026.10.1%2B-blue"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/marketplace_repository/?owner=gszigethy&repository=HA-Webasto-Cool-Top-Trail&category=integration"><img alt="Open in the Marketplace" src="https://my.home-assistant.io/badges/marketplace_repository.svg"></a>
  <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=webasto_cool_top_trail"><img alt="Add integration" src="https://my.home-assistant.io/badges/config_flow_start.svg"></a>
</p>

<p align="center">
  <a href="#️-how-it-works">How it works</a> ·
  <a href="#-what-you-need">What you need</a> ·
  <a href="#-installation">Installation</a> ·
  <a href="#-troubleshooting">Troubleshooting</a> ·
  <a href="#-more-information">More information</a>
</p>
<!-- ha-marketplace:exclude-end -->

<p align="center"><strong>Control your Webasto Cool Top Trail caravan or motorhome air conditioner from Home Assistant,<br>the same way the handheld remote does.</strong></p>

✅ **Tested on a real air conditioner.** Every control works. See the [testing status](docs/validation.md).

🏠 **Fully local.** No cloud, no account, no pairing, no button learning.

## ⚙️ How it works

```text
Home Assistant  ──Wi-Fi──▶  ESP32  ──infrared──▶  air conditioner
                              ▲
             handheld remote ─┘ (optional IR receiver)
```

| Part | Job |
| --- | --- |
| 📡 **ESP32** with an **infrared (IR) LED** | Acts as the remote control. You set it up with ESPHome. |
| 🧩 **This integration** | Adds the air-conditioner controls to Home Assistant and tells the ESP32 what to send. |
| 👁️ **IR receiver** (optional) | Lets Home Assistant follow presses on the handheld remote. |

## ✨ What you get

| Control | What it does |
| --- | --- |
| 🌡️ **Climate** | Off, cool, heat, auto (heat/cool), dry, fan only. Temperature in °C or °F, fan speed, Sleep. |
| 🔒 **Panel display, Panel control lock** | Switch the AC's display off, lock its buttons. |
| ⏰ **On timer, Off timer, On time, Off time** | The AC's own daily timers. |
| 🔌 **Protocol status** | Shows whether the ESP32 is connected and ready. |

> **Note:** Infrared only goes one way. The AC never reports back, so Home Assistant shows the settings it last sent, not confirmed AC status.

## 🧰 What you need

- **Home Assistant** 2026.10.1 or newer. From 2026.11 the **Marketplace** is built in; on 2026.10 you need **[HACS](https://hacs.xyz/)**.
- **ESPHome** 2026.9.1 or newer, for example the ESPHome Device Builder add-on in Home Assistant.
- An **ESP32** board with an **IR transmitter LED** pointed at the AC.
- Optional: an **IR receiver** on the same ESP32.
- The GPIO pin numbers your transmitter (and receiver) are connected to.

## 🚀 Installation

Five steps: **ESP32 → add it to Home Assistant → install this integration → add the AC → first use.**

### Step 1: Set up the ESP32

1. In **ESPHome Device Builder**, create a new device and open its YAML editor. Copy the `key:` value under `api:` → `encryption:` before replacing anything.
2. Replace the whole YAML with the example below (also on GitHub: **[esp32/example.yaml](https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail/blob/main/esp32/example.yaml)**).
3. Follow the comments in it: change the pins and board, and remove the receiver parts if you have no IR receiver.
4. Open **Secrets** in Device Builder and make sure it has `wifi_ssid`, `wifi_password` and `api_encryption_key`. Use the key you copied in point 1 for `api_encryption_key`.
5. Click **Install**. The first install usually needs a USB cable; later updates work over Wi-Fi.

```yaml
# Webasto Cool Top Trail IR bridge for Home Assistant.
# Paste this into ESPHome Device Builder, then:
#   1. CHANGE the pins and the board below to match your hardware.
#   2. No IR receiver? REMOVE the two parts marked "Only with an IR receiver".
#   3. Add wifi_ssid, wifi_password and api_encryption_key under Secrets in
#      Device Builder (use the API key Device Builder generated for this device).
# Keep the send_frame action and sensor names: the integration finds them by name.

substitutions:
  device_name: webasto-ir-bridge       # CHANGE if you like: network name
  friendly_name: Webasto IR Bridge     # CHANGE if you like: name shown in Home Assistant
  transmitter_pin: GPIO26              # CHANGE: GPIO of your IR LED
  receiver_pin: GPIO32                 # CHANGE: GPIO of your IR receiver

esphome:
  name: ${device_name}
  friendly_name: ${friendly_name}
  min_version: 2026.9.1

esp32:
  board: esp32dev                      # CHANGE: your board, e.g. m5stack-atom
  framework:
    type: esp-idf

# Downloads only the IR codec (webasto_ir.h) from GitHub. Nothing else is fetched.
external_components:
  - source: github://gszigethy/HA-Webasto-Cool-Top-Trail@main
    components: [webasto_ir]

webasto_ir:

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

logger:

ota:
  - platform: esphome

api:
  encryption:
    key: !secret api_encryption_key
  reboot_timeout: 0s                   # Keep running when Home Assistant is out of reach.
  actions:
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
              # Longest frame is 251 ms; report the result once it has been sent.
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

text_sensor:
  - platform: template
    id: transmitted_frame
    name: Transmitted IR frame
    entity_category: diagnostic
    update_interval: never
  # --- Only with an IR receiver: remove this sensor if you have none ---
  - platform: template
    id: received_frame
    name: Received IR frame
    entity_category: diagnostic
    update_interval: never

# --- Only with an IR receiver: remove this whole section if you have none ---
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

ESPHome downloads only the IR codec (`webasto_ir.h`) from this repository, through `external_components:`. Everything else is in this one file, and you don't place any file manually.

### Step 2: Add the ESP32 to Home Assistant

Go to **Settings → Devices & services**. The ESP32 usually appears as a discovered **ESPHome** device; click **Add**. If it doesn't, choose **Add integration → ESPHome** and enter its IP address. Use the API encryption key from step 1 if asked.

### Step 3: Install this integration

Download **Webasto Cool Top Trail** from the Marketplace (or HACS), then **restart Home Assistant**.

<!-- ha-marketplace:exclude-start -->
The integration is in the default Marketplace and HACS store, so you don't need to add a custom repository.

Home Assistant 2026.11 or newer:

[![Open in the Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=gszigethy&repository=HA-Webasto-Cool-Top-Trail&category=integration)

1. Click the button above, or open **Settings → Marketplace** and search for **Webasto Cool Top Trail**.
2. Download it and **restart Home Assistant**.

Home Assistant 2026.10 with HACS:

1. Open **HACS** and search for **Webasto Cool Top Trail**.
2. Download it and **restart Home Assistant**.
<!-- ha-marketplace:exclude-end -->

### Step 4: Add the air conditioner

<!-- ha-marketplace:exclude-start -->
[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=webasto_cool_top_trail)
<!-- ha-marketplace:exclude-end -->

Click the button above, or go to **Settings → Devices & services → Add integration → Webasto Cool Top Trail**, and fill in:

- **Name:** for example "Caravan AC".
- **ESPHome IR bridge:** the ESP32 from step 2.
- **Room temperature sensor:** optional, only used to show the current temperature.

### Step 5: First use

The controls are available right away, with or without a receiver. They start from default settings: **off, heat/cool, 22 °C, high fan**. Nothing is sent until you use a control.

With a receiver, whenever someone uses the handheld remote, Home Assistant picks up the remote's settings automatically.

🎉 Now try turning the AC on from Home Assistant and check that the AC responds.

## 💡 Good to know

- Every command sends **all** the AC's settings at once and sets the AC's clock. If someone uses the handheld remote and Home Assistant doesn't hear it, the next command from Home Assistant overwrites that change.
- Home Assistant doesn't see the AC's own timers switching it on or off.
- The ESP32 keeps working when Home Assistant is unreachable; it simply waits for the next command.

## 🔧 Troubleshooting

| Problem | What to check |
| --- | --- |
| Setup says the device has no `send_frame` action | The ESP32 is online and was installed with the example YAML above |
| Controls are unavailable / **Bridge disconnected** | The ESP32's power and Wi-Fi |
| Home Assistant changes but the AC doesn't | The transmitter pin, wiring, and that the IR LED points at the AC |

More help: [installation guide](docs/installation.md#if-something-does-not-work).

## 📚 More information

- [Detailed installation and everyday use](docs/installation.md)
- [Entities and automation examples](docs/entity-map.md)
- [ESPHome files explained](esp32/README.md)
- [How the IR protocol was decoded](docs/ir-protocol.md)
- [Testing status](docs/validation.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)
- [Manufacturer's manual (Hungarian)](https://varadicaravan.hu/wp-content/uploads/2022/04/Webasto-Cool-Top-Trail-20_24.pdf)

## 🙏 Credits

- **[IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266)** by [@crankyoldgit](https://github.com/crankyoldgit) and contributors: the `CARRIER_AC128` protocol and its wire timings, which identified this remote's signal.
- **[@mrmees](https://github.com/mrmees)**: the [esphome-houghton-ac](https://github.com/mrmees/esphome-houghton-ac) project and its byte-level analysis of the Houghton protocol ([#2009](https://github.com/crankyoldgit/IRremoteESP8266/issues/2009), [#2247](https://github.com/crankyoldgit/IRremoteESP8266/issues/2247)), the main field-map reference.
- **[@MarkEvens](https://github.com/MarkEvens)**: the original report that led to `CARRIER_AC128` being identified ([#1797](https://github.com/crankyoldgit/IRremoteESP8266/issues/1797)).
- **Webasto**: the "W" logo used as the integration icon, from their CC0 [Webasto Logo 2024.svg](https://commons.wikimedia.org/wiki/File:Webasto_Logo_2024.svg).
- **[Home Assistant](https://www.home-assistant.io/)**, **[ESPHome](https://esphome.io/)** and **[HACS](https://hacs.xyz/)** (now the Marketplace), which this integration builds on.

Webasto and Cool Top Trail are trademarks of their respective owners. This is an independent community project, not affiliated with or endorsed by Webasto or Houghton.
