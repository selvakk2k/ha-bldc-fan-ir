# Indian BLDC Fan Integration (`ha-bldc-fan-ir`)

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/superfan_ir/brand/dark_logo.png">
    <img alt="Indian BLDC Fan Integration Logo" src="custom_components/superfan_ir/brand/logo.png" width="340">
  </picture>
</p>

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)
[![Stable](https://img.shields.io/github/v/release/selvakk2k/ha-bldc-fan-ir?label=Stable&style=flat-square)](https://github.com/selvakk2k/ha-bldc-fan-ir/releases/latest)
[![Beta](https://img.shields.io/github/v/release/selvakk2k/ha-bldc-fan-ir?include_prereleases&label=Beta&color=orange&style=flat-square)](https://github.com/selvakk2k/ha-bldc-fan-ir/releases)
[![AI-Assisted](https://img.shields.io/badge/AI%20Assisted-Antigravity%20%7C%20Claude-blueviolet?style=flat-square&logo=google)](https://github.com/selvakk2k)
[![AI Attribution](https://img.shields.io/badge/AI%20Attribution-AIA%20PAI%20Nc%20Hin-orange?style=flat-square)](https://aiattribution.github.io/interpret-attribution)

A Home Assistant custom integration for controlling Indian BLDC ceiling fans (Atomberg, Superfan, Orient, Activa, Goldmedal) via Infrared (IR) blasters. This integration provides native `fan` platform entities with accurate speed tiers, timer modes, smart power switch bindings, and multi-format blaster support.

> [!TIP]
> A companion Lovelace dashboard card is available: **[bldc-fan-card](https://github.com/selvakk2k/bldc-fan-card)** (Indian BLDC Fan Card).

> [!NOTE]
> ### Upgrading from 1.x to 2.0
> Upgrading requires zero configuration changes. The integration domain remains `superfan_ir`. All existing fan entities, speed presets, and automations continue working as before. Version 2.0 expands support to Atomberg, Orient, Activa, and Goldmedal ceiling fans, and adds dynamic multi-blaster dispatch (ESPHome, Broadlink, Tuya).

---

## Table of Contents

1. [Key Features](#key-features)
2. [Supported Fan Brands & Remote Models](#supported-fan-brands--remote-models)
3. [IR Blaster Compatibility & Formats](#ir-blaster-compatibility--formats)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [ESPHome Blaster Configuration Examples](#esphome-blaster-configuration-examples)
7. [Troubleshooting & Logs](#troubleshooting--logs)
8. [My Integrations & Lovelace Cards](#my-integrations--lovelace-cards)
9. [Credits & License](#credits--license)

---

## Key Features

### 1. Multi-Format IR Dispatch
Transmit commands using any common smart IR blaster hardware without needing manual code learning:
* **Native Home Assistant Infrared (`ir_rf_proxy` - Recommended):** Uses Home Assistant's native `infrared` platform to send microsecond timing arrays directly to ESPHome or native transmitter entities.
* **Broadlink:** Transmits base64 Pronto-encoded packets via Broadlink RM4/RM mini remotes.
* **Tuya Base64:** Sends compressed Tuya IR packets to Tuya-based Zigbee/Wi-Fi blasters (`remote.send_command`).
* **Tasmota / MQTT:** Dispatches raw or NEC hex strings over MQTT to Tasmota-flashed IR bridges.

### 2. Smart Switch Power Management
If your ceiling fan is connected through a physical smart switch or relay (e.g. Sonoff, Shelly, Tuya):
* **State Restoration & Sync:** The fan automatically restores its last-known speed percentage and state upon Home Assistant restart, and immediately reflects physical wall switch flips.
* **Auto Power-on with Boot Delay:** Turning on the fan or changing speeds automatically powers on the physical wall switch and waits for the fan's receiver microcontroller to initialize (configurable 1–3 seconds) before transmitting the IR payload.
* **Power-Off Bypass:** Turning the fan off cuts physical power immediately via the smart switch, saving standby power without relying on optical line-of-sight.

### 3. Symmetrical Diagnostics & Telemetry
Exposes last control source tracking and connection state sensors to monitor blaster responsiveness on your dashboard.

---

## Supported Fan Brands & Remote Models

During setup, select the remote model mapping matching your physical ceiling fan:

| Brand / Family | Remote Model | Speed Levels | Presets & Capabilities | Verified Hardware |
| :--- | :--- | :--- | :--- | :--- |
| **Atomberg** | Standard BLDC Remote | 6 Speeds (1–6 + Boost) | Boost Mode, Sleep Mode, Timer (1h, 2h, 3h, 6h), LED Toggle | ✅ Renesa, Efficio, Aris, Studio, Erica |
| **Superfan** | T10 Remote | 5 Speeds (1–5) | Breeze Mode, Speed Adjust, 2h Timer, 6h Timer | ✅ Super X, A, V, J, P, Visree T6/P6 |
| **Superfan** | T12/6 Remote | 3 Speeds (Low, Med, High) | Breeze Mode, Eco Mode, Sleep Mode, Reverse Mode, Wellness, AC Mix, 2h/6h Timer | ✅ Super Q Series |
| **Orient** | BLDC Remote | 5 Speeds (1–5 + Boost) | Breeze Mode, Sleep Mode, Boost Mode, Timer (2h, 4h, 6h, 8h) | ✅ I-Tome, Aeroslim, Wendy, Ecotech |
| **Activa** | BLDC Remote | 6 Speeds (1–6 + Boost) | Boost Mode, Sleep Mode, Timer (1h, 2h, 4h, 8h) | ✅ Gracia, Energia, Apsara |
| **Goldmedal** | BLDC Remote | 6 Speeds (1–6) | Sleep Mode, Breeze Mode, Timer (2h, 4h, 6h, 8h), LED Light | ✅ Opus Prime, Winzo, Spacio, Aura Lux |

> [!NOTE]
> Models not listed in this table are not blocked. Any ceiling fan utilizing the same brand remote protocol will function normally. The table above lists physically tested units, not a hard compatibility limit.

---

## IR Blaster Compatibility & Formats

The integration automatically generates and encodes signals for all supported blaster hardware—no manual code learning or YAML packet crafting is required. In the setup wizard, simply select your existing `remote.*` or `infrared.*` entity:
* **Auto-Detect**: Automatically identifies your blaster type (ESPHome, Broadlink, or Tuya) directly from the selected entity, with manual override available if desired.

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant Fan Entity                │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   [Native HA Infrared]                   [Remote Platform]
    • ir_rf_proxy                          • Broadlink Base64
    • Microsecond Timing Arrays            • Tuya Base64
                                           • Pronto Hex
                                           • Tasmota / MQTT
```

---

## Installation

* **Prerequisites**: Home Assistant **2024.1.0** or newer.

### Method 1: Using HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=selvakk2k&repository=ha-bldc-fan-ir&category=integration)

1. Click the **Open repository in HACS** button above, or open **HACS** from your Home Assistant sidebar.
2. Click the top-right menu (⋮) → **Custom repositories** → Add `https://github.com/selvakk2k/ha-bldc-fan-ir` with category **Integration**.
3. Search for **Indian BLDC Fan IR**, click **Download**, and restart Home Assistant.

### Method 2: Manual Installation
1. Download the latest release ZIP from the [Releases](https://github.com/selvakk2k/ha-bldc-fan-ir/releases) page.
2. Copy the `custom_components/superfan_ir` folder into your Home Assistant `<config>/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
2. Search for **Indian BLDC Fan IR**.
3. In **Step 1: Indian BLDC Fan Setup (Optical IR)**:
   * **Fan Name**: Friendly name for this fan entity (e.g. *Living Room Fan*).
   * **Fan Brand & Remote Model**: Select your fan brand and remote model (e.g. *Atomberg BLDC*, *Superfan T10*, *Orient BLDC*).
   * **IR Format**: Select the signal encoding format expected by your blaster (`Auto-Detect`, `Home Assistant Infrared / ESPHome Raw`, `Broadlink Base64`, `Tuya Base64`, or `Tasmota / MQTT`).
4. In **Step 2: Select IR Transmitter**:
   * **IR Transmitter Entity**: Select your `infrared.*` or `remote.*` blaster entity.
   * **Availability / Status Entity (Optional)**: Select an availability entity (`binary_sensor`, `input_boolean`, `switch`, or `device_tracker`, such as a smart plug, network router tracker, or helper) to detect blaster outages immediately without waiting for Home Assistant's default 90-120 second TCP timeout. Standard state values (`on`, `home`, `connected`) indicate the blaster is online and available; any other state marks it offline.
5. *(Optional Options Flow)*: Click **Configure** on the fan card to adjust settings or bind an **IR Receiver Entity (Optional)**, **Power Switch Entity (Optional)**, or **Availability Entity (Optional)**.


---

## ESPHome Blaster Configuration Examples

For the best latency and reliability, use the native `ir_rf_proxy` component in ESPHome:

```yaml
remote_receiver:
  id: ir_rx
  pin:
    number: GPIO14
    inverted: true
    mode: INPUT_PULLUP

remote_transmitter:
  id: ir_tx
  pin: GPIO12
  carrier_duty_percent: 50%

# Exposes native infrared entities to Home Assistant
infrared:
  - platform: ir_rf_proxy
    name: "Living Room IR Transmitter"
    remote_transmitter_id: ir_tx
  - platform: ir_rf_proxy
    name: "Living Room IR Receiver"
    receiver_frequency: 38kHz
    remote_receiver_id: ir_rx
```

### ESPHome 2026.10+ Upgrade & Firmware Notes
* **ESPHome 2026.10+ Upgrade (Recommended)**: For native `infrared` transmitters, upgrading the blaster to ESPHome `2026.10` or newer enables hardware transmit-complete acknowledgements. The integration automatically detects firmware 2026.10+ and applies an explicit 2.5-second completion timeout to command dispatch, immediately marking the entity offline if transmission fails.
* **LibreTiny Buffer Size Change (PR #19101)**: If using Beken BK7231N (LibreTiny) or ESP8266 hardware with an explicit `buffer_size` configured under `remote_receiver:`, note that ESPHome 2026.10 measures buffer capacity in bytes rather than entry count. Multiply your existing `buffer_size` value by 4 (e.g. from `1000` to `4000`) when upgrading your YAML configuration to ESPHome 2026.10+. If `buffer_size` is omitted in your YAML, no change is needed.

---

## Troubleshooting & Logs

### 1. Enabling Debug Logs

#### Via the UI (Dynamic, no restart required)
1. Go to **Settings → Devices & Services** → Select the **Indian BLDC Fan IR** card.
2. Click the top-right menu (**⋮**) → **Enable debug logging**.
3. Trigger commands from the dashboard, then click **Disable debug logging** to download the log file.

#### Via `configuration.yaml` (Persistent / Startup Issues)
To view detailed dispatch and decoding logs across Home Assistant restarts, add this to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.superfan_ir: debug
```

### 2. IR Blaster Troubleshooting
* **Transmitter Line-of-Sight**: Verify your IR blaster LED has an unobstructed line of sight to the fan motor housing or canopy sensor dome.
* **Carrier Frequency**: Ensure your receiver/transmitter hardware is configured for **38 kHz** modulated carrier frequency.
* **Raw Protocol**: For ESPHome devices with native `infrared` components, select **Raw** or **Auto-Detect** in the integration configuration for microsecond-precise hardware pulsing.

---

## My Integrations & Lovelace Cards

| Integration / Card | Category | Description | Status |
| :--- | :--- | :--- | :--- |
| [CP PLUS STQC](https://github.com/selvakk2k/ha-cpplus-stqc) | Integration | Local NVR & STQC IP Camera integration with real-time AI push events | `Beta` |
| [Panasonic AC India](https://github.com/selvakk2k/ha-panasonic-ac-in) | Integration | Local IR & Cloud MQTT control for Panasonic MirAIe Air Conditioners | `Stable` |
| [Panasonic AC India Card](https://github.com/selvakk2k/panasonic-ac-card-in) | Lovelace Card | Modern Lovelace card for Panasonic ACs | `Stable` |
| [Indian BLDC Fan IR](https://github.com/selvakk2k/ha-bldc-fan-ir) | Integration | Native Home Assistant integration for Indian BLDC ceiling fans (Atomberg, Superfan) | `Stable` |
| [Indian BLDC Fan Card](https://github.com/selvakk2k/bldc-fan-card) | Lovelace Card | Interactive Lovelace card with speed dial & mode toggles for BLDC fans | `Stable` |
| [IFB Washer Local](https://github.com/selvakk2k/ifb-washer-local) | Integration | Local Wi-Fi integration for IFB Front Load Washing Machines & Washer Dryers | `Beta` |
| [IFB Washer Card](https://github.com/selvakk2k/ifb-washer-card) | Lovelace Card | Dedicated Lovelace card for IFB washers & dryers with cycle controls | `Beta` |
| [Tinxy Local Python](https://github.com/selvakk2k/ha-tinxylocal) | Integration | Pure-Python local control for Tinxy smart switches and modules | `Stable` |

---

## Credits & License

### Project Contributors & AI Attribution
* **Lead Architecture & Hardware Validation**: [@selvakk2k](https://github.com/selvakk2k) — physical remote captures, protocol verification on hardware units, and domain architecture.
* **Code Implementation & Engineering**: **Antigravity** (Google DeepMind) — multi-brand protocol decoders, native `infrared` platform integration, and config flows.
* **Pre-Release Code Review & Auditing**: **Claude** (Anthropic) — independent code review, timing accuracy audits, and edge-case verification.

Licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
