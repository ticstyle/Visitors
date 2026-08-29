# custom_components/visitors/device_tracker.py
"""Device tracker platform for Visitors."""

from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
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


class VisitorsVirtualTracker(TrackerEntity, RestoreEntity):
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
        self._zone_name = zone_name
        self._zone_slug = zone_slug
        self._trackers = trackers
        self._attr_unique_id = f"{config_entry.entry_id}_manual_tracker"

        # Explicitly apply requested custom naming scheme
        self._attr_name = f"Visitors at {zone_name}"
        self.entity_id = f"device_tracker.visitors_at_{zone_slug}"
        self._attr_location_name = STATE_NOT_HOME

        if zone == "zone.home" or zone.endswith(".home"):
            self._zone_state_name = STATE_HOME
        else:
            self._zone_state_name = zone_name

    def _get_switch_entity_id(self) -> str:
        """Fetch the live companion switch entity ID from the entity registry."""
        entity_reg = er.async_get(self.hass)
        if switch_id := entity_reg.async_get_entity_id(
            SWITCH_DOMAIN, DOMAIN, f"{self._config_entry.entry_id}_manual_switch"
        ):
            return switch_id
        return f"switch.visitors_at_{self._zone_slug}"

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

    async def async_added_to_hass(self) -> None:
        """Handle entity which is about to be added to hass."""
        await super().async_added_to_hass()

        # Restore last known location name from state machine cache
        if (
            (old_state := await self.async_get_last_state()) is not None
            and old_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
        ):
            self._attr_location_name = old_state.state

        @callback
        def async_state_changed_listener(event: Event[EventStateChangedData]) -> None:
            """Handle changes from manual switch or monitored device trackers."""
            self.async_schedule_update_ha_state(True)

        # Monitor both manual toggle switch and physical device trackers
        entities_to_track = list(self._trackers) + [self._get_switch_entity_id()]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entities_to_track, async_state_changed_listener
            )
        )

        self.async_schedule_update_ha_state(True)

    async def async_update(self) -> None:
        """Update tracker status based on companion switch or presence of guest trackers."""
        switch_on = False
        switch_state = self.hass.states.get(self._get_switch_entity_id())
        if switch_state and switch_state.state == "on":
            switch_on = True

        tracker_in_zone = False
        for tracker_id in self._trackers:
            state = self.hass.states.get(tracker_id)
            if state and state.state == self._zone_state_name:
                tracker_in_zone = True
                break

        # Set location name according to target zone rules
        if switch_on or tracker_in_zone:
            if self._zone == "zone.home" or self._zone.endswith(".home"):
                self._attr_location_name = STATE_HOME
            else:
                self._attr_location_name = self._zone_name
        else:
            self._attr_location_name = STATE_NOT_HOME
