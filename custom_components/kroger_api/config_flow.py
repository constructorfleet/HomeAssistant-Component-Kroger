import logging

import voluptuous as vol
from homeassistant.const import (CONF_CLIENT_ID, CONF_CLIENT_SECRET)
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)


@callback
def register_flow_implementation(hass: HomeAssistantType,
                                 client_id: str,
                                 client_secret: str):
    """Register a kroger api implementation.
    client_id: Client id.
    client_secret: Client secret.
    """
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN] = {
        CONF_CLIENT_ID: client_id,
        CONF_CLIENT_SECRET: client_secret
    }


class KrogerApiConfigFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
                                 domain=DOMAIN):
    """Handle Kroger API flow."""

    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return await super().async_step_user(user_input)

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create an oauth config entry or update existing entry for reauth."""
        existing_entry = await self.async_set_unique_id(DOMAIN)
        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")
        return self.async_create_entry(title="KrogerAPI", data=data)
