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

    if not isinstance(zone, str):
        _LOGGER.error("Monitored zone is missing or invalid")
        return

    # Fetch zone friendly name for custom explicit naming
    zone_state = hass.states.get(zone)
    zone_name = (
        zone_state.attributes.get("friendly_name")
        if zone_state and zone_state.attributes.get("friendly_name")
        else zone.split(".")[-1].replace("_", " ").title()
    )
    zone_slug = slugify(zone_name)

    sensor = VisitorsSensor(config_entry, zone, zone_name, zone_slug, trackers)
    async_add_entities([sensor], update_before_add=True)


class VisitorsSensor(SensorEntity):
    """Representation of a Visitors Sensor."""

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "visitors"
    _attr_icon = "mdi:account-group"

    def __init__(
        self,
        config_entry: ConfigEntry,
        zone: str,
        zone_name: str,
        zone_slug: str,
        trackers: list[str],
    ) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._zone = zone
        self._trackers = trackers
        self._attr_unique_id = f"{config_entry.entry_id}_sensor"

        # Explicitly apply requested custom naming scheme
        self._attr_name = f"Visitors at {zone_name}"
        self.entity_id = f"sensor.visitors_at_{zone_slug}"
        self._switch_entity_id = f"switch.visitors_at_{zone_slug}"

        self._zone_state_name = zone.split(".")[-1]
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
            """Handle state changes of tracked entities and companion switch."""
            self.async_schedule_update_ha_state(True)

        # Track both the physical entities and our manual helper switch state
        entities_to_track = list(self._trackers) + [self._switch_entity_id]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entities_to_track, async_state_changed_listener
            )
        )

    async def async_update(self) -> None:
        """Update the visitor count state."""
        count = 0
        for tracker_id in self._trackers:
            state = self.hass.states.get(tracker_id)
            if state and state.state == self._zone_state_name:
                count += 1

        # Append manual override weight if switch is active
        switch_state = self.hass.states.get(self._switch_entity_id)
        if switch_state and switch_state.state == "on":
            count += 1

        self._state = count
        
