"""Sensor platform for Visitors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import CONF_TRACKERS, CONF_ZONE, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Visitors sensor platform."""
    zone = config_entry.options.get(CONF_ZONE, config_entry.data.get(CONF_ZONE))
    trackers = config_entry.options.get(
        CONF_TRACKERS, config_entry.data.get(CONF_TRACKERS, [])
    )

    tracked_entities = list(trackers)
    # Always append our companion manual guest tracker to our monitoring checklist
    title_slug = slugify(config_entry.title)
    manual_tracker_id = f"device_tracker.visitors_manual_{title_slug}"
    if manual_tracker_id not in tracked_entities:
        tracked_entities.append(manual_tracker_id)

    sensor = VisitorsSensor(config_entry, zone, tracked_entities)
    async_add_entities([sensor], update_before_add=True)


class VisitorsSensor(SensorEntity):
    """Representation of a Visitors Sensor."""

    _attr_has_entity_name = True
    _attr_translation_key = "visitors_count"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "visitors"
    _attr_icon = "mdi:account-group"

    def __init__(
        self,
        config_entry: ConfigEntry,
        zone: str,
        trackers: list[str],
    ) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._zone = zone
        self._trackers = trackers
        self._attr_unique_id = f"{config_entry.entry_id}_sensor"
        # Extract location state name from zone entity ID (e.g., zone.home -> home)
        self._zone_state_name = zone.split(".")[-1] if zone else "home"
        self._state: int | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=self._config_entry.title,
            manufacturer="ticstyle",
            model="Visitors",
        )

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "monitored_zone": self._zone,
            "tracked_entities": self._trackers,
        }

    async def async_added_to_hass(self) -> None:
        """Handle entity which is about to be added to hass."""
        await super().async_added_to_hass()

        @callback
        def async_state_changed_listener(event: Event[EventStateChangedData]) -> None:
            """Handle state changes of tracked entities."""
            self.async_schedule_update_ha_state(True)

        # Bind state listener to all tracked device entities
        if self._trackers:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self._trackers, async_state_changed_listener
                )
            )

    async def async_update(self) -> None:
        """Update the visitor count state and sync virtual person states."""
        count = 0
        title_slug = slugify(self._config_entry.title)
        manual_tracker_id = f"device_tracker.visitors_manual_{title_slug}"

        for tracker_id in self._trackers:
            state = self.hass.states.get(tracker_id)
            if state and state.state == self._zone_state_name:
                count += 1

            # Skip our manual tracker (it's updated in device_tracker.py directly)
            if tracker_id == manual_tracker_id:
                continue

            tracker_name = tracker_id.split(".")[-1]
            person_entity_id = f"person.visitors_tracker_{tracker_name}"

            # Check if this tracker is already linked to a native HA resident person
            is_already_tracked = False
            for p_state in self.hass.states.async_all("person"):
                # Ignore our own virtual entities to prevent false positive matches
                if p_state.entity_id.startswith(
                    "person.visitors_"
                ) or p_state.entity_id.startswith("person.visitors_manual_"):
                    continue
                if p_state.attributes.get("source") == tracker_id:
                    is_already_tracked = True
                    break

            if not is_already_tracked:
                target_state = state.state if state else "not_home"
                friendly_name = (
                    state.attributes.get(
                        "friendly_name", tracker_name.replace("_", " ").title()
                    )
                    if state
                    else tracker_name.replace("_", " ").title()
                )

                in_zones_list = (
                    [self._zone] if target_state == self._zone_state_name else []
                )

                self.hass.states.async_set(
                    person_entity_id,
                    target_state,
                    {
                        "friendly_name": f"Guest ({friendly_name})",
                        "icon": "mdi:account-badge",
                        "editable": False,
                        "in_zones": in_zones_list,
                    },
                )
            else:
                # If a resident links it later, immediately clean up our duplicate
                self.hass.states.async_remove(person_entity_id)

        # Clean up any virtual visitor people whose trackers were removed from the options flow
        active_person_ids = {
            f"person.visitors_tracker_{t_id.split('.')[-1]}"
            for t_id in self._trackers
            if t_id != manual_tracker_id
        }
        for state in self.hass.states.async_all("person"):
            if (
                state.entity_id.startswith("person.visitors_tracker_")
                and state.entity_id not in active_person_ids
            ):
                self.hass.states.async_remove(state.entity_id)

        self._state = count
