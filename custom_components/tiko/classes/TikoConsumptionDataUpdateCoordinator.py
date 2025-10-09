"""Tiko Consumption Data Update Coordinator - Improved version."""
from datetime import timedelta
import logging

import async_timeout

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from ..const import CONF_API_URL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..api import getConsumptionData, login

_LOGGER = logging.getLogger(__name__)


class TikoConsumptionDataUpdateCoordinator(DataUpdateCoordinator):
    """Tiko consumption data coordinator with improved error handling."""

    def __init__(self, hass, config_entry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="TikoConsumptionDataUpdateCoordinator",
            update_interval=timedelta(minutes=5),  # Update every 5 minutes
            always_update=True,
        )
        self._config_entry = config_entry
        self._credentials = None
        self._data = None
        self._apiUrl = self._config_entry.data.get(CONF_API_URL, None)
        self._login_attempts = 0
        self._max_login_attempts = 3

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(15):
                # Login if needed
                if self._credentials is None:
                    _LOGGER.debug("No credentials, attempting login")
                    self._credentials = await self._async_login()

                    if not self._credentials:
                        raise UpdateFailed("Failed to login to Tiko API")

                # Get consumption data for today
                new_data = await getConsumptionData(
                    self._apiUrl,
                    self._credentials,
                    period="today"
                )

                if new_data is None:
                    # Try to re-login once if data fetch fails
                    _LOGGER.warning("Failed to get consumption data, attempting re-login")
                    self._credentials = None
                    self._credentials = await self._async_login()

                    if self._credentials:
                        new_data = await getConsumptionData(
                            self._apiUrl,
                            self._credentials,
                            period="today"
                        )

                if new_data is not None:
                    self._data = new_data
                    self._login_attempts = 0  # Reset login attempts on success
                    _LOGGER.debug("Successfully updated consumption data")
                    return self._data
                else:
                    # Return last known data if available
                    if self._data is not None:
                        _LOGGER.warning("Using cached consumption data")
                        return self._data
                    raise UpdateFailed("No consumption data available")

        except async_timeout.TimeoutError as err:
            _LOGGER.error("Timeout fetching consumption data: %s", err)
            if self._data is not None:
                return self._data
            raise UpdateFailed("Timeout fetching consumption data") from err
        except Exception as err:
            _LOGGER.error("Error fetching consumption data: %s", err)
            if self._data is not None:
                return self._data
            raise UpdateFailed(f"Error fetching consumption data: {err}") from err

    async def _async_login(self):
        """Handle login with retry logic."""
        if self._login_attempts >= self._max_login_attempts:
            _LOGGER.error(
                "Max login attempts (%d) reached, stopping retries",
                self._max_login_attempts
            )
            return None

        self._login_attempts += 1

        try:
            credentials = await login(
                self._apiUrl,
                self._config_entry.data[CONF_USERNAME],
                self._config_entry.data[CONF_PASSWORD],
            )

            if credentials:
                _LOGGER.info("Successfully logged in to Tiko API")
                return credentials
            else:
                _LOGGER.error("Login failed, attempt %d/%d",
                              self._login_attempts, self._max_login_attempts)
                return None

        except Exception as err:
            _LOGGER.error("Login error: %s", err)
            return None