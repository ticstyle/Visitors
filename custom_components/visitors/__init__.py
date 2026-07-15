"""The Visitors integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_CREATE_MANUAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Visitors from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    platforms = list(PLATFORMS)
    # Check if we should spin up the manual guest tracker components
    if entry.options.get(CONF_CREATE_MANUAL, entry.data.get(CONF_CREATE_MANUAL, True)):
        platforms.extend([Platform.SWITCH, Platform.DEVICE_TRACKER])

    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    # Listen for configuration option updates to reload on the fly
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    platforms = list(PLATFORMS)
    if entry.options.get(CONF_CREATE_MANUAL, entry.data.get(CONF_CREATE_MANUAL, True)):
        platforms.extend([Platform.SWITCH, Platform.DEVICE_TRACKER])

    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
