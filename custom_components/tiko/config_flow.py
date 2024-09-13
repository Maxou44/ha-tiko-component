import voluptuous as vol
from .api import login
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
)

import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TikoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Tiko configuration flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """The user should fill the email and password of the Tiko account."""
        errors = {}

        self.username = ""
        self.password = ""

        if user_input is not None:
            self.username = user_input[CONF_USERNAME]
            self.password = user_input[CONF_PASSWORD]

            # Try to login
            tokens = await login(self.username, self.password)
            if not tokens:
                errors["base"] = "auth"
            else:
                return self.async_create_entry(
                    title=DOMAIN,
                    data={
                        CONF_USERNAME: self.username,
                        CONF_PASSWORD: self.password,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self.username): str,
                    vol.Required(CONF_PASSWORD, default=self.password): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Retourne l'option pour gérer la configuration après le setup."""
        return TikoOptionsFlow(config_entry)


class TikoOptionsFlow(config_entries.OptionsFlow):
    """Gère le flow d'options pour Tiko."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Gère les options supplémentaires (si nécessaire)."""
        return self.async_show_form(step_id="init")
