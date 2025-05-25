# Cupra Formentor Integration for Home Assistant

[![Version](https://img.shields.io/github/v/release/cfpandrade/cupra_formentor)](https://github.com/cfpandrade/cupra_formentor/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

This integration provides support for the **Cupra Formentor** in Home Assistant, specifically adapted from the original Cupra WeConnect integration.

## 🚗 Supported Vehicles

- **Cupra Formentor 2021+** (Hybrid and Electric versions)

## ✨ Features

| Platform | Description |
|----------|-------------|
| `sensor` | Retrieves and displays vehicle information |
| `binary_sensor` | Monitors vehicle status, such as door locks and battery levels |
| `button` | Allows for remote actions like starting/stopping charging or climatization |
| `number` | Configures values such as target SOC and climate temperature |
| `device_tracker` | Tracks the location of your vehicle |

## 📦 Installation

### Via HACS (Recommended)

1. Open [HACS](https://hacs.xyz/) in Home Assistant
2. Search for "Cupra Formentor" and install the integration
3. Follow the [Configuration](#configuration) steps below

If the integration does not appear in HACS, manually add `https://github.com/cfpandrade/cupra_formentor` as a custom repository.

### Manual Installation

1. Navigate to your Home Assistant configuration directory
2. Create a `custom_components/cupra_formentor` folder if it does not exist
3. Download and place all repository files in this folder
4. Restart Home Assistant and follow the [Configuration](#configuration) steps

## ⚙️ Configuration

### Prerequisites

- Ensure that the **Cupra We Connect app** is set up and used at least once
- Accept all terms and conditions in the app

### Setup

1. Navigate to **Settings → Integrations** in Home Assistant
2. Add the "Cupra Formentor" integration and enter your login credentials
3. Wait for the vehicle to appear with its entities

### Troubleshooting Authentication

If authentication fails:

1. Log in at [Cupra We Connect](https://cupraid.vwgroup.io/account)
2. Accept any pending terms and conditions
3. Temporarily change your country/region, save, log out, and log back in
4. Revert country/region changes and reload the Cupra integration

## 🔧 Requirements

- **Cupra Formentor 2021+**
- **Home Assistant Core 2022.7.0** or later
- Valid **Cupra WeConnect** account

## 🆕 What's New in v0.2.0

- ✅ **Updated to official WeConnect library** (stable and maintained)
- ✅ **Fixed hybrid vehicle support** (handles None values correctly)
- ✅ **Improved error handling** and logging
- ✅ **Better Formentor-specific naming** and services
- ✅ **Enhanced reliability** and performance

## 🐛 Known Issues

- Login throttling may occur with multiple authentication attempts
- Some features may not be available for hybrid vehicles vs fully electric

## 🙏 Credits

Special thanks to:
- **@mitch-dc** for the VW ID integration foundation
- **@tillsteinbach** for the WeConnect Python library
- **Alan Gibson** for adapting it to Cupra
- **@daernsinstantfortress** for the original Cupra WeConnect integration

This version has been specifically tailored for **Cupra Formentor** by @cfpandrade.

## 📄 License

This project is licensed under the MIT License.
