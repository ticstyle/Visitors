# Visitors

<p align="center">
  <img src="custom_components/visitors/brand/logo.png" alt="Visitors Logo" width="600">
</p>

  ![Release](https://img.shields.io/github/v/release/ticstyle/Visitors?style=for-the-badge&color=blue)
  ![HA Integration](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue?style=for-the-badge&logo=home-assistant)
  [![Hassfest](https://img.shields.io/github/actions/workflow/status/ticstyle/Visitors/pipeline.yml?branch=main&job=hassfest&label=Hassfest&style=for-the-badge)](https://github.com/ticstyle/Visitors/actions/workflows/pipeline.yml)
  [![HACS Validation](https://img.shields.io/github/actions/workflow/status/ticstyle/Visitors/pipeline.yml?branch=main&job=hacs&label=HACS&style=for-the-badge)](https://github.com/ticstyle/Visitors/actions/workflows/pipeline.yml)
  [![Ruff / Format](https://img.shields.io/github/actions/workflow/status/ticstyle/Visitors/pipeline.yml?branch=main&job=sync_and_format&label=Ruff%20%2F%20Format&style=for-the-badge)](https://github.com/ticstyle/Visitors/actions/workflows/pipeline.yml)
  [![Mypy](https://img.shields.io/github/actions/workflow/status/ticstyle/Visitors/pipeline.yml?branch=main&job=mypy&label=Mypy&style=for-the-badge)](https://github.com/ticstyle/Visitors/actions/workflows/pipeline.yml)
  ![License](https://img.shields.io/github/license/ticstyle/Visitors?style=for-the-badge)
  ![Installs](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=41BDF5&logo=home-assistant&label=installs&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.Visitors.total)
  ![Issues](https://img.shields.io/github/issues/ticstyle/Visitors?style=for-the-badge&color=orange)

An elegant, lightweight Home Assistant custom integration to track guest occupancy without messy templates, groups, or hardcoded automations. **Visitors** dynamically aggregates any selection of physical device trackers alongside a virtual guest presence helper to give you a single, reliable state metric representing the exact number of visitors currently inside a targeted zone.

To add this integration, search for `Visitors` in HACS or add this repository custom URL: `https://github.com/ticstyle/Visitors`

---

## ✨ Features

* 📍 **Zone-Agnostic Aggregation:** Define which specific zone represents your target area (`zone.home` is set as default), allowing you to build dedicated trackers for vacation homes, work locations, or standard residences.
* 👥 **Dynamic Tracker Binding:** Select any number of standard `device_tracker` entities to track. The parent sensor automatically monitors status shifts across all of them and counts how many are concurrently inside the selected zone boundaries.
* 🔘 **Manual Guest Toggle Engine:** Need to track a visitor who doesn't have a device tracker integrated? The integration can dynamically spin up a companion virtual guest presence switch (`switch.visitors_manual_...`) and linked virtual tracker (`device_tracker.visitors_manual_...`) inside Home Assistant on demand. Flipping the switch automatically checks a virtual guest in or out of the target zone.
* ⚡ **Event-Driven & Polling-Free:** Built entirely with asynchronous event hooks. The integration does not run continuous CPU-heavy polling intervals; it updates immediately when Home Assistant reports state changes for any of your selected trackers.
* 🛠️ **Seamless Options Flow:** Reconfigure your zone targets, change which trackers are being aggregated, or toggle the virtual manual guest components on the fly directly through the Home Assistant integrations configuration card.

---

## 🚀 Installation

### Via HACS (Recommended)
You can search for the **Visitors** integration directly within HACS or launch it immediately using the button below:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ticstyle&repository=Visitors&category=Integration)

### Manual Installation
1. Download the [latest release](https://github.com/ticstyle/Visitors/releases/latest) zip file.
2. Extract the `visitors` directory into your Home Assistant `<config_dir>/custom_components/` folder.
3. Restart Home Assistant to register the custom integration files.

---

## ⚙️ Configuration

[![Open your Home Assistant instance and start a setting flow for a specific integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=visitors)

1. Navigate to **Settings -> Devices & Services -> Add Integration** in your Home Assistant UI.
2. Search for **Visitors** and click setup.
3. Complete the setup form by configuring your tracker targets:
   * **Name**: The display name for your integration device container (defaults to `Visitors`).
   * **Zone**: The target `zone.*` to monitor.
   * **Device Trackers**: A multi-select checklist of your physical device trackers.
   * **Manual Guest Switch**: Toggle whether you want the integration to create a local virtual device tracker and toggle switch.

---

## 📊 Available Entities

The integration creates a unified device named **Visitors** holding up to three entities (depending on whether your manual guest switch was activated during configuration):

| Entity ID | Name in UI | State Example | Description |
| :--- | :--- | :--- | :--- |
| `sensor.visitors_<entry_id>_sensor` | Visitors | `3` | Displays the current number of active tracked guests located within the target zone. |
| `switch.visitors_manual_<entry_id>` | Manual Guest Presence | `on` *(På)* | A virtual toggle switch. When turned `on`, it checks the manual guest tracker into the target zone. |
| `device_tracker.visitors_manual_<entry_id>` | Manual Guest | `home` | A virtual device tracker that mimics the state of the companion toggle switch. |

### Entity Attributes
The core sensor entity exposes structural tracking metadata under its state attributes:
* `monitored_zone`: The configured target zone entity ID (e.g., `zone.home`).
* `tracked_entities`: A list of all targeted device trackers currently being monitored.

---

## 💡 Lovelace Dashboard Examples

### Example 1: Sleek Clean Header Card
Display a welcoming greeting on your main dashboard showing the exact occupancy state of your home.

```yaml
type: markdown
title: "House Status"
content: >
  ### 🏡 Welcome Home!
  
  Currently, there are **{{ states('sensor.visitors') }}** visitor(s) checked in at our residence.
  
  {% if is_state('switch.visitors_manual_presence', 'on') %}
    📌 A manual guest has been checked in by a host toggle.
  {% endif %}
```

### Example 2: Interactive Guest Management Hub
An elegant control center to check manual visitors in and out of your home on the fly.

```yaml
type: entities
title: "👥 Guest Management"
show_header_toggle: false
entities:
  - entity: sensor.visitors
    name: "Active Guest Count"
    icon: mdi:account-group
  - type: section
    label: "Manual Controls"
  - entity: switch.visitors_manual_presence
    name: "Toggle Temporary Guest"
    icon: mdi:account-plus
  - entity: device_tracker.visitors_manual
    name: "Virtual Tracker State"
```

### Example 3: Conditional Lovelace Guest Banner
Display a dynamic alert banner at the top of your dashboard that only triggers when visitors are detected at your home.

```yaml
type: conditional
conditions:
  - condition: numeric_state
    entity: sensor.visitors
    above: 0
card:
  type: markdown
  content: >
    🔔 **Visitor Mode Active:** Automations adjusted for guest occupancy (e.g., motion timeouts extended, night scenes delayed).
```
