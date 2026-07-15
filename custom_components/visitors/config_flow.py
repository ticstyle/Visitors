"""Config flow for Visitors integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CREATE_MANUAL,
    CONF_TRACKERS,
    CONF_ZONE,
    DEFAULT_NAME,
    DEFAULT_ZONE,
    DOMAIN,
)


class VisitorsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Visitors."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            title = user_input.get("name", DEFAULT_NAME)
            return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_ZONE, default=DEFAULT_ZONE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="zone")
                ),
                vol.Optional(CONF_TRACKERS, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="device_tracker", multiple=True
                    )
                ),
                vol.Required(
                    CONF_CREATE_MANUAL, default=True
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return VisitorsOptionsFlowHandler(config_entry)


class VisitorsOptionsFlowHandler(OptionsFlow):
    """Handle Visitors options modifications."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        # Store config entry privately to avoid conflicting with base class property
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the updated configuration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Retrieve current configuration or fall back to original data setup
        current_zone = self._config_entry.options.get(
            CONF_ZONE, self._config_entry.data.get(CONF_ZONE, DEFAULT_ZONE)
        )
        current_trackers = self._config_entry.options.get(
            CONF_TRACKERS, self._config_entry.data.get(CONF_TRACKERS, [])
        )
        current_create_manual = self._config_entry.options.get(
            CONF_CREATE_MANUAL,
            self._config_entry.data.get(CONF_CREATE_MANUAL, True),
        )

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ZONE, default=current_zone
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="zone")
                ),
                vol.Optional(
                    CONF_TRACKERS, default=current_trackers
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="device_tracker", multiple=True
                    )
                ),
                vol.Required(
                    CONF_CREATE_MANUAL, default=current_create_manual
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
