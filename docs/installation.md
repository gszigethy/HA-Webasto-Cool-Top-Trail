# Install and use Webasto Cool Top Trail

This guide takes you from an ESP32 with infrared hardware to an air-conditioner control in Home Assistant. You do not need to understand the IR protocol or record every remote button.

The integration is still in development. Its software and recorded remote signals have been tested, but generated commands have not yet been checked on the actual air conditioner. Support for other Houghton models is not confirmed.

## How it works

Home Assistant tells your ESP32 what settings to send. The ESP32's infrared transmitter sends them to the air conditioner, like the handheld remote does.

There are two pieces to install:

| Piece | Where it runs | What it does |
| --- | --- | --- |
| ESPHome configuration | On your ESP32 | Connects to Wi-Fi and sends infrared commands |
| Webasto Cool Top Trail integration | In Home Assistant, installed through HACS | Adds the climate control, timers, and other controls |

An **IR transmitter** is the part that sends infrared light. An **IR receiver** is an optional part that listens to the handheld remote. A receiver helps Home Assistant follow remote changes; it does not receive status reports from the air conditioner.

There is no pairing with the air conditioner and no button-by-button learning. The integration already knows how to build commands for the supported remote protocol.

## Before you start

You need:

- Home Assistant 2026.10.1 or newer, with HACS installed.
- ESPHome 2026.9.1 or newer. You can manage the ESP32 using ESPHome Device Builder or the ESPHome command-line tool.
- An ESP32 with a working IR transmitter and a suitable power supply.
- The GPIO number connected to your transmitter. If you also have a receiver, you need its GPIO number too.
- Wi-Fi credentials for the ESP32's location.

GPIO numbers identify connection pins on the ESP32. They are board-specific: the numbers in our example are not instructions for every board. This repository does not supply a universal wiring diagram or transmitter circuit; use the wiring instructions for your hardware.

**Already have an ESPHome IR transmitter?** It still needs this project's sending action. An existing setup that sends a few fixed button recordings will not provide everything this integration needs. Back up its configuration before changing it, and retain any unrelated functions on that ESP32.

Choose your setup:

| Your hardware | What to do |
| --- | --- |
| Transmitter only | Follow the steps below and remove the receiver parts of the example; the integration then starts from default settings automatically |
| Transmitter and receiver | Keep the receiver section; you can initialize settings by pressing a button on the handheld remote |

## 1. Prepare the ESP32

### Copy the device YAML

Create a device in ESPHome Device Builder and paste the contents of
[bridge.example.yaml](../esp32/bridge.example.yaml) into its YAML editor.

ESPHome downloads the shared IR configuration and C++ code from GitHub when you
validate or install the device. **You do not need to download or place a header
file.** The computer running Device Builder needs internet access for that download;
the ESP32 controls the AC locally after installation.

This package-based example was added after **1.0.0 beta 1**. Its `webasto_ref: main`
uses the current repository configuration. Do not change it to `v1.0.0-beta.1`,
which does not contain the packages. Future releases can be selected by changing
this value to their tag.

### Set your device name and pins

At the top of the YAML, change the following values to suit your hardware:

```yaml
substitutions:
  device_name: webasto-ir-bridge
  friendly_name: Webasto IR Bridge
  receiver_pin: GPIO32
  transmitter_pin: GPIO26
```

- `device_name` is the ESP32's network name. Keeping `webasto-ir-bridge` makes the examples later in this guide match your setup.
- `friendly_name` is the name you will see in Home Assistant.
- `transmitter_pin` must match the pin connected to your IR transmitter.
- `receiver_pin` must match your receiver, if fitted.

The example uses GPIO26 for sending and GPIO32 for receiving because those were used on the debugging hardware. They are not universal defaults. The original caravan prototype used GPIO2 for sending.

Also check the `esp32` board setting against your board. The example uses `esp32dev` with the ESP-IDF framework.

**If you have no receiver:** remove the `esp32/packages/receiver.yaml` line from the `packages` list. The optional `receiver_pin` substitution can also be removed. The sending action and Transmitted IR frame sensor remain in the bridge package automatically.

Keep the sensor names and the `send_frame` action name as in the example. The integration finds them on the ESP32 by these names.

**If updating an existing ESPHome device:** add the example's `packages:` block and pin substitutions to your existing YAML. Keep your existing board, Wi-Fi, API encryption, OTA and other hardware settings. If your YAML already has `packages:` or `substitutions:`, add to those sections instead of creating a second copy. The package supplies `api.reboot_timeout: 0s`; keep this value if you also set it locally. Remove the old `includes: webasto_ir.h` entry and old Webasto sending action, sensors and receiver/transmitter blocks before using the package, to avoid duplicate IDs. Unrelated IR functions may need their existing receiver/transmitter blocks merged with the package by ID. Stop using the old fixed-command buttons or automations to control the AC once you switch to the new climate control.

### Add Wi-Fi details and an encryption key

In the same folder, add these entries to `secrets.yaml`, using your own values:

```yaml
caravan_wifi_ssid: "YOUR_WIFI_NAME"
caravan_wifi_password: "YOUR_WIFI_PASSWORD"
api_encryption_key: "YOUR_ESPHOME_API_ENCRYPTION_KEY"
```

The API encryption key protects the connection between Home Assistant and your ESP32. Use the key generated for your device by ESPHome Device Builder, or retain its existing key when updating a device. It is not your Wi-Fi password. Do not use the placeholder key in this repository's example secrets file.

If your existing configuration uses different secret names, either change the YAML references to match them or add the three entries above. Keep your real credentials private.

### Install the configuration on the ESP32

In ESPHome Device Builder, validate the device configuration, then use **Install** to build and install it. A new device usually needs its first installation over USB; an existing connected ESPHome device can use a wireless update. Installing firmware replaces what currently runs on the ESP32.

If you use the command line instead:

```bash
esphome config bridge.example.yaml
esphome compile bridge.example.yaml
esphome upload bridge.example.yaml
```

Replace `bridge.example.yaml` with your actual YAML filename if you renamed it.

**Before continuing:** the ESP32 should be connected to Wi-Fi and shown as online in ESPHome. You have installed the sending firmware, but have not yet added the Webasto climate control.

## 2. Connect the ESP32 to Home Assistant

Open **Settings → Devices & services** in Home Assistant.

If the ESP32 is discovered, add it using the **ESPHome** integration. Otherwise, choose **Add integration → ESPHome** and enter the ESP32's hostname or IP address. If asked for the encryption key, use the same API key you put in `secrets.yaml`.

Open the new ESPHome device. With the default friendly name, you should find:

- **Webasto IR Bridge Transmitted IR frame**
- **Webasto IR Bridge Received IR frame**, only if your ESP32 has a receiver

These are diagnostic sensors. A “frame” means one complete infrared command. Their contents are technical data used by the integration; you do not need to read or edit them.

Both may initially show **Unknown**. That is normal before any command has been received or sent. **Unavailable** means Home Assistant cannot currently access the device or sensor.

The ESP32 also provides a sending action. To check it, open **Developer tools → Actions** and search for `send_frame`. With the example device name, the action is:

```text
esphome.webasto_ir_bridge_send_frame
```

You do not need to run this action yourself. The Webasto integration will use it. If it is missing, check that the ESP32 is connected and that you installed the bridge configuration, rather than the separate research/capture firmware.

## 3. Download the integration through HACS

1. Open **HACS** and its menu for **Custom repositories**.
2. Enter `https://github.com/gszigethy/HA-Webasto-Cool-Top-Trail`.
3. Choose **Integration** as the category and add it.
4. Find **Webasto Cool Top Trail** in HACS and download it. While no release is published, use the `main` version if prompted.
5. Restart Home Assistant.

Downloading through HACS installs the Home Assistant part. It does not install or update your ESP32 firmware.

If you do not use HACS, copy the repository's `custom_components/webasto_cool_top_trail` folder into Home Assistant's `config/custom_components` folder and restart. The remaining steps are the same. You do not need to add this integration to `configuration.yaml`.

## 4. Add Webasto Cool Top Trail

Go to **Settings → Devices & services → Add integration**, search for **Webasto Cool Top Trail**, and open it.

Fill in the fields as follows:

| Field shown in setup | What to choose |
| --- | --- |
| **Name** | A name for your AC, such as “Caravan AC” |
| **ESPHome IR bridge** | The ESP32 you connected in step 2, for example **Webasto IR Bridge** |
| **Room temperature sensor (optional)** | An existing sensor that measures the temperature inside your caravan in °C or °F. Leave it empty if you do not have one |

The integration finds the rest on that ESP32 by itself: its sending action, and its **Received IR frame** sensor if it has one. If setup says the device has no `send_frame` action, check that the ESP32 is online and runs the bridge configuration.

### How Home Assistant gets its first settings

Every command sends the AC's complete settings, so Home Assistant needs a starting point:

- **With a receiver:** press any button on the handheld remote once, pointed at the receiver. Home Assistant takes over all of the remote's settings.
- **Without a receiver:** Home Assistant starts from default settings automatically.

The default settings are:

- Power off; cooling mode ready for the next turn-on.
- 24 °C, automatic fan, Sleep off.
- Panel display on and panel controls unlocked.
- Both timers disabled, with stored on/off times of 09:00 and 10:00.

**Setup does not send anything to the AC.** Your first operation of a control sends the complete set of settings, including the defaults you have not changed. For example, turning on starts cooling at 24 °C with automatic fan.

The integration remembers subsequent settings across Home Assistant restarts. Default settings are the starting point, not a reset on every restart.

## 5. Try the climate control

After setup, open the **Webasto Cool Top Trail** device in Home Assistant. It has a climate control plus switches, timer times, and a status sensor.

**If using a receiver:** point the handheld remote at the receiver and press a normal AC button. The integration reads its settings and makes the climate control available. Celsius and Fahrenheit remote settings are both supported.

**If using a transmitter alone:** the climate control becomes available as soon as the ESP32 is connected.

Place the transmitter so its infrared light can reach the air conditioner's receiver. Try a simple operation, such as turning the AC on, and check the appliance itself for a response. A change on the Home Assistant card alone does not prove the AC received the command.

Add the climate entity to your dashboard if you want quick access. The other controls are available on the device page and can also be added to a dashboard or automation.

## Everyday use

### Temperature, modes, and fan

Use the climate control to turn the AC on or off, choose its mode, set the temperature, and choose the fan speed.

- The remote's automatic operating mode appears as **Heat/cool** in Home Assistant. It uses one target temperature.
- **Auto fan** is a separate setting, available in heating and cooling.
- **Dry** uses low fan speed.
- **Fan only** has no temperature setting.
- **Sleep** is available during heating and cooling.
- Turning off keeps your other settings. Turning on resumes the stored mode.
- Changing the temperature while the climate entity is off keeps it off.

Home Assistant displays temperatures in your preferred units. Commands retain the remote's Celsius or Fahrenheit setting, in one-degree steps: 16–30 °C or 60–86 °F. There is no separate control for changing the AC's display between °C and °F; use the handheld remote for that. If a receiver hears the change, the integration follows it.

A current room temperature is only shown if you selected a real temperature sensor. The remote signal does not contain a room-temperature measurement.

### Panel display and lock

**Panel display** controls the display on the air conditioner's air-distribution panel. **Panel control lock** locks or unlocks that panel's touch controls.

### On/off timers

Set **On time** or **Off time**, then enable the corresponding **On timer** or **Off timer** switch. Both can be enabled. Disabling a timer keeps its stored time for later use.

These are the air conditioner's own daily timers, using local hours and minutes. Every command Home Assistant sends refreshes the appliance clock from HA local time. There is no separate clock-sync action.

Home Assistant cannot see the AC switching itself on or off when a timer fires, so the climate card may still show the last commanded state. It also does not run these timers itself. The physical AC's timer behavior remains part of the pending appliance tests.

### Using the handheld remote as well

With a receiver, commands that it hears update Home Assistant's settings. The receiver needs to be positioned where it can see the remote's infrared light.

Without a receiver, Home Assistant cannot know about changes made using the remote. Its next command sends all of its saved settings and may overwrite those changes. This is also possible if a fitted receiver misses a remote press.

The system never receives confirmation of actual cooling, heating, compressor operation, or appliance faults over IR.

## If something does not work

| What you see | What to try |
| --- | --- |
| Setup says the device has no `send_frame` action | Check that the ESP32 is online and its configuration includes the example's `api:` sending action, named `send_frame` |
| **Awaiting remote frame** | Point the remote at the receiver and press a button. If you removed the receiver, check that you also removed the **Received IR frame** sensor, then reload the integration |
| **Bridge disconnected**, or unavailable controls | Check power, Wi-Fi, the ESPHome connection, and that setup points to the correct ESP32 |
| **Received IR frame** shows **Unknown** | No valid remote command has been heard yet |
| You added or removed the receiver later | Update the ESP32 firmware, then reload the Webasto integration so it notices the change |
| Current temperature is missing | Choose an actual room-temperature sensor in setup; check that it is available and reports °C or °F |
| The Home Assistant card changes but the AC does not | Check the transmitter wiring and GPIO, power supply, and its position relative to the AC. Confirm it is a working IR transmitter |
| Remote presses do not update Home Assistant | Check receiver wiring and position. Incomplete or noisy commands are ignored |
| The card does not change when an AC timer fires | Expected: the appliance does not report timer events back to Home Assistant |

The **Protocol status** sensor helps distinguish a disconnected ESP32 from a connected system waiting for its first remote command. **Ready** means the integration has a connection and settings it can send; it does not mean the air conditioner has confirmed anything.

To change your choices, open **Settings → Devices & services**, find the Webasto integration entry, and choose **Reconfigure** from its menu. You can change the name, the selected ESP32, or the room-temperature sensor. Clear the optional room sensor to remove it.

If reporting a problem, include your AC/remote model, ESP32 board, transmitter/receiver pins, ESPHome version, and what happened at the appliance. Remove passwords and encryption keys from any configuration or logs you share.

## More detail

- [Controls and automation examples](entity-map.md)
- [ESPHome files and capture tools](../esp32/README.md)
- [IR protocol](ir-protocol.md)
- [Functional design](functional-design.md) and [technical design](technical-design.md)
- [Software checks and physical appliance tests](validation.md)
