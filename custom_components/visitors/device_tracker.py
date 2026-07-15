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

from .const import CONF_ZONE, DEFAULT_ZONE, DOMAIN

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
    tracker = VisitorsVirtualTracker(config_entry, zone)
    async_add_entities([tracker], update_before_add=True)


class VisitorsVirtualTracker(TrackerEntity):
    """Representation of a virtual guest device tracker."""

    _attr_has_entity_name = True
    _attr_translation_key = "manual_guest_tracker"
    _attr_icon = "mdi:account"

    def __init__(self, config_entry: ConfigEntry, zone: str) -> None:
        """Initialize the device tracker."""
        self._config_entry = config_entry
        self._zone = zone
        self._zone_state_name = zone.split(".")[-1] if zone else "home"
        self._attr_unique_id = f"{config_entry.entry_id}_manual_tracker"
        self._title_slug = slugify(config_entry.title)
        self.entity_id = f"device_tracker.visitors_manual_{self._title_slug}"
        self._switch_entity_id = f"switch.visitors_manual_{self._title_slug}"
        self._state = "not_home"

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
    def in_zones(self) -> list[str] | None:
        """Return the zones the device is in."""
        if self._state == self._zone_state_name:
            return [self._zone]
        return []

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device."""
        return SourceType.ROUTER

    async def async_added_to_hass(self) -> None:
        """Handle entity which is about to be added to hass."""
        await super().async_added_to_hass()

        @callback
        def async_switch_state_listener(event: Event[EventStateChangedData]) -> None:
            """Handle switch state changes to sync the tracker state."""
            self.async_schedule_update_ha_state(True)

        # Track the paired switch entity to update the tracker location
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._switch_entity_id], async_switch_state_listener
            )
        )

    async def async_update(self) -> None:
        """Update the tracker state based on the companion switch."""
        switch_state = self.hass.states.get(self._switch_entity_id)
        if switch_state and switch_state.state == "on":
            self._state = self._zone_state_name
        else:
            self._state = "not_home"

        # Dynamically create/sync a virtual person entity in the state machine.
        # This forces HA's native zone occupancy count to update automatically.
        in_zones_list = [self._zone] if self._state == self._zone_state_name else []
        self.hass.states.async_set(
            f"person.visitors_manual_{self._title_slug}",
            self._state,
            {
                "friendly_name": f"Guests ({self._config_entry.title})",
                "icon": "mdi:account-group",
                "editable": False,
                "in_zones": in_zones_list,
            },
        )
