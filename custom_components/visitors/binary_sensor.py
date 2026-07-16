"""Binary sensor platform for Visitors."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up the Visitors binary sensor platform."""
    zone = config_entry.options.get(CONF_ZONE, config_entry.data.get(CONF_ZONE))
    trackers = config_entry.options.get(
        CONF_TRACKERS, config_entry.data.get(CONF_TRACKERS, [])
    )

    if not isinstance(zone, str):
        _LOGGER.error("Monitored zone is missing or invalid")
        return

    zone_state = hass.states.get(zone)
    zone_name = zone.split(".")[-1].replace("_", " ").title()
    if zone_state and isinstance(
        friendly_name := zone_state.attributes.get("friendly_name"), str
    ):
        zone_name = friendly_name
    zone_slug = slugify(zone_name)

    # Instantiate a binary presence entity for every monitored physical tracker
    binary_sensors = [
        VisitorBinarySensor(config_entry, zone, zone_name, zone_slug, tracker_id)
        for tracker_id in trackers
    ]

    async_add_entities(binary_sensors, update_before_add=True)


class VisitorBinarySensor(BinarySensorEntity):
    """Representation of an individual guest presence binary sensor."""

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_icon = "mdi:account-presence"

    def __init__(
        self,
        config_entry: ConfigEntry,
        zone: str,
        zone_name: str,
        zone_slug: str,
        tracker_id: str,
    ) -> None:
        """Initialize the guest binary sensor."""
        self._config_entry = config_entry
        self._zone = zone
        self._zone_name = zone_name
        self._tracker_id = tracker_id

        tracker_slug = tracker_id.split(".")[-1]
        self._attr_unique_id = f"{config_entry.entry_id}_binary_{tracker_slug}"

        # Keep entity ID fully stable using the raw slugs so automations never break
        self.entity_id = f"binary_sensor.visitor_{zone_slug}_{tracker_slug}"

        self._zone_state_name = zone.split(".")[-1]
        self._is_on = False

    @property
    def name(self) -> str:
        """Dynamically fetch name from live state to capture upstream renames."""
        state = self.hass.states.get(self._tracker_id)
        if state and isinstance(
            friendly_name := state.attributes.get("friendly_name"), str
        ):
            return f"{friendly_name} at {self._zone_name}"

        fallback_name = self._tracker_id.split(".")[-1].replace("_", " ").title()
        return f"{fallback_name} at {self._zone_name}"

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
    def is_on(self) -> bool:
        """Return True if the specific guest is in the target zone."""
        return self._is_on

    async def async_added_to_hass(self) -> None:
        """Handle entity which is about to be added to hass."""
        await super().async_added_to_hass()

        @callback
        def async_tracker_state_listener(event: Event[EventStateChangedData]) -> None:
            """Instantly update state when the specific target tracker shifts."""
            self.async_schedule_update_ha_state(True)

        # Track only our specific targeted device tracker
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._tracker_id], async_tracker_state_listener
            )
        )

    async def async_update(self) -> None:
        """Evaluate whether this targeted device is currently inside the zone boundaries."""
        state = self.hass.states.get(self._tracker_id)
        self._is_on = bool(state and state.state == self._zone_state_name)
