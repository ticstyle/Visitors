"""Device tracker platform for Visitors."""

from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import CONF_TRACKERS, CONF_ZONE, DEFAULT_ZONE, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Visitors device tracker platform."""
    zone = config_entry.options.get(
        CONF_ZONE, config_entry.data.get(CONF_ZONE, DEFAULT_ZONE)
    )
    trackers = config_entry.options.get(
        CONF_TRACKERS, config_entry.data.get(CONF_TRACKERS, [])
    )

    if not isinstance(zone, str):
        _LOGGER.error("Monitored zone is missing or invalid")
        return

    # Fetch zone friendly name for custom explicit naming
    zone_state = hass.states.get(zone)
    zone_name = zone.split(".")[-1].replace("_", " ").title()
    if zone_state and isinstance(
        friendly_name := zone_state.attributes.get("friendly_name"), str
    ):
        zone_name = friendly_name
    zone_slug = slugify(zone_name)

    tracker = VisitorsVirtualTracker(config_entry, zone, zone_name, zone_slug, trackers)
    async_add_entities([tracker], update_before_add=True)


class VisitorsVirtualTracker(TrackerEntity):
    """Representation of a virtual guest device tracker."""

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_icon = "mdi:account"

    def __init__(
        self,
        config_entry: ConfigEntry,
        zone: str,
        zone_name: str,
        zone_slug: str,
        trackers: list[str],
    ) -> None:
        """Initialize the device tracker."""
        self._config_entry = config_entry
        self._zone = zone
        self._trackers = trackers
        self._zone_state_name = zone.split(".")[-1]
        self._attr_unique_id = f"{config_entry.entry_id}_manual_tracker"

        # Explicitly apply requested custom naming scheme
        self._attr_name = f"Visitors at {zone_name}"
        self.entity_id = f"device_tracker.visitors_at_{zone_slug}"
        self._switch_entity_id = f"switch.visitors_at_{zone_slug}"
        self._active = False

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
    def source_type(self) -> SourceType:
        """Return the source type of the device."""
        return SourceType.ROUTER

    @property
    def in_zones(self) -> list[str] | None:
        """Return the zones the device is currently in to drive native person tracking."""
        if self._active:
            return [self._zone]
        return []

    async def async_added_to_hass(self) -> None:
        """Handle entity which is about to be added to hass."""
        await super().async_added_to_hass()

        @callback
        def async_state_changed_listener(event: Event[EventStateChangedData]) -> None:
            """Handle changes from manual switch or monitored device trackers."""
            self.async_schedule_update_ha_state(True)

        # Monitor both the manual toggle switch and our physical device trackers list
        entities_to_track = list(self._trackers) + [self._switch_entity_id]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entities_to_track, async_state_changed_listener
            )
        )

    async def async_update(self) -> None:
        """Update tracker status based on companion switch or presence of guest trackers."""
        switch_on = False
        switch_state = self.hass.states.get(self._switch_entity_id)
        if switch_state and switch_state.state == "on":
            switch_on = True

        tracker_in_zone = False
        for tracker_id in self._trackers:
            state = self.hass.states.get(tracker_id)
            if state and state.state == self._zone_state_name:
                tracker_in_zone = True
                break

        # Sync the internal presence state to trigger the native property calculation
        self._active = bool(switch_on or tracker_in_zone)
