# Visitors

<p align="left">
  <img src="https://github.com/ticstyle/Visitors/blob/main/custom_components/visitors/brand/logo.png" alt="Visitors Logo" width="800">
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

An elegant, lightweight Home Assistant custom integration to track guest occupancy without messy templates, groups, or hardcoded automations. **Visitors** dynamically aggregates any selection of physical device trackers alongside a manual guest presence toggle to give you a single, reliable state metric representing the exact number of visitors currently inside a targeted zone.

To add this integration, search for `Visitors` in HACS or add this repository custom URL: `https://github.com/ticstyle/Visitors`

---

## ✨ Features

* 📍 **Zone-Agnostic Aggregation:** Define which specific zone represents your target area (`zone.home` is set as default), allowing you to build dedicated trackers for vacation homes, work locations, or standard residences.
* 👥 **Dynamic Tracker Binding:** Select any number of standard `device_tracker` entities to track. The parent sensor automatically monitors status shifts across all of them and counts how many are concurrently inside the selected zone boundaries.
* 🛡️ **Dynamic Child Presence Sensors:** Automatically generates an individual binary sensor for every single selected device tracker. These entities utilize the native `presence` device class to display clean, localized **Home** / **Away** states, while listening live to upstream name updates so display profiles stay perfectly in sync.
* 🔘 **Built-in Manual Guest Engine:** Need to track a visitor who doesn't have a device tracker integrated? The integration automatically spins up a dedicated manual companion switch and a virtual device tracker for each instance.
* 🔀 **Composite Presence Logic:** The virtual guest device tracker intelligently turns `home` if the manual switch is flipped `on` **OR** if any of your monitored physical trackers arrive in the zone (even if the manual switch remains off).
* 🧮 **Additive Counting Metrics:** The core sensor acts as a true mathematical sum, counting the manual switch as one visitor (when active) plus each chosen physical device tracker currently inside the zone (e.g. scales effortlessly from 0 to 19+ visitors).
* ⚡ **Event-Driven & Polling-Free:** Built entirely with asynchronous event hooks. The integration does not run continuous CPU-heavy polling intervals; it updates immediately when Home Assistant reports state changes.

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
   * **Zone to monitor**: The target `zone.*` to monitor (e.g., `zone.home`). 
   * **Device trackers to track**: A multi-select checklist of your physical guest device trackers.
4. The integration automatically resolves the zone name and names the instance `"Visitors at <Zone Name>"` with clean, readable entity handles.

---

## 🔝 Native Zone Occupancy Setup (Highly Recommended)

Home Assistant's native zone state counter (e.g., `zone.home`) is strictly hardcoded to **only count system-registered `person` entities**. It completely ignores raw sensors or standalone device trackers.

To make this integration automatically scale your home's official zone occupancy count whenever a guest arrives or the switch is toggled, execute this quick **30-second, one-time manual setup**:

1. Go to **Settings -> People** in your Home Assistant UI and click **Add Person**.
2. Name the person something clean like **Guests** or **Visitors**.
3. In the **"Track device"** dropdown, search for and select the virtual tracker generated by this integration: `device_tracker.visitors_at_<choosen_zone_name>`.
4. Click **Save**.

Now, whenever the companion switch is toggled or an assigned device tracker enters the zone, the virtual tracker handles the person state behind the scenes, instantly incrementing your native `zone.home` occupant counter!

---

## 📊 Available Entities

The integration creates a unified device named **Visitors at <Zone Name>** holding cleanly mapped entities. Examples below use `zone.home` yielding the slug `home` and track a device named `stacey_phone`:

| Entity ID | Name in UI | State Example | Description |
| :--- | :--- | :--- | :--- |
| `sensor.visitors_at_home` | Visitors at Home | `3` | Displays the total count of active guest device trackers in the zone + the manual switch status weight. |
| `switch.visitors_at_home` | Manually set visitors at Home | `on` | A helper toggle switch to manually inject guest presence without a physical device tracker. |
| `device_tracker.visitors_at_home` | Visitors at Home | `home` | A composite virtual device tracker driven by the manual switch state and active guest tracker arrivals. |
| `binary_sensor.visitor_home_stacey_phone` | Stacey Phone at Home | `on` *(Home)* | Individual status indicator for a specific guest device tracker within this zone. Native presence class maps translation to Home/Away. |

### Entity Attributes
The core sensor entity exposes structural tracking metadata under its state attributes:
* `monitored_zone`: The configured target zone entity ID (e.g., `zone.home`).
* `tracked_entities`: A list of all targeted physical device trackers currently being monitored.

---

## 💡 Lovelace Dashboard Examples

### Example 1: High-Visibility Glance Grid
An elegant visual status hub showing the collective counter alongside individual guest presence badges that light up when active.

```yaml
type: glance
title: "👥 Guest Room Presence"
state_color: true
entities:
  - entity: sensor.visitors_at_home
    name: Total Visitors
  - entity: binary_sensor.visitor_home_stacey_phone
    name: Stacey
  - entity: switch.visitors_at_home
    name: Manual Toggle
```

### Example 2: Minimalist Management Card
Display a welcoming greeting on your main dashboard showing the exact occupancy state of your home with conditional warnings.

```yaml
type: entities
title: "🏡 Occupancy Management"
show_header_toggle: false
entities:
  - entity: sensor.visitors_at_home
    name: "Active Guest Count"
    icon: mdi:account-group
  - type: section
    label: "Manual Override"
  - entity: switch.visitors_at_home
    name: "Check In Temporary Guest"
    icon: mdi:account-plus
```

### Example 3: Conditional Lovelace Guest Banner
Display a dynamic alert banner at the top of your dashboard that only triggers when visitors are detected at your home.

```yaml
type: conditional
conditions:
  - condition: numeric_state
    entity: sensor.visitors_at_home
    above: 0
card:
  type: markdown
  content: >
    🔔 **Visitor Mode Active:** Automations adjusted for guest occupancy (e.g., motion timeouts extended, night scenes delayed).
```
