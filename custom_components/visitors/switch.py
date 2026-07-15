"""Switch platform for Visitors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Visitors switch platform."""
    switch = VisitorsManualSwitch(config_entry)
    async_add_entities([switch])


class VisitorsManualSwitch(SwitchEntity):
    """Representation of a manual visitor toggle switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "manual_guest_toggle"
    _attr_icon = "mdi:account-arrow-right"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the switch."""
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_manual_switch"
        title_slug = slugify(config_entry.title)
        self.entity_id = f"switch.visitors_manual_{title_slug}"
        self._is_on = False

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
        """Return True if entity is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._is_on = False
        self.async_write_ha_state()
