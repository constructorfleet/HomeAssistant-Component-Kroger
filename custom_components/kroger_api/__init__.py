import voluptuous as vol
from aiohttp.client import DEFAULT_TIMEOUT
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_PLATFORM, CONF_TIMEOUT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import HomeAssistantType, ConfigType

from .api import KrogerApiOAuth2Implementation, ConfigEntryKrogerApiClient
from .config_flow import KrogerApiConfigFlowHandler
from .const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN
)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): DOMAIN,
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    }
)


async def async_setup(hass: HomeAssistantType,
                      config: ConfigType):
    """Set up the Kroger API component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    KrogerApiConfigFlowHandler.async_register_implementation(
        hass,
        KrogerApiOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    return True
