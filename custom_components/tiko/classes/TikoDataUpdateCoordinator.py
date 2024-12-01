from datetime import timedelta, datetime
import logging

import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from ..const import CONF_API_URL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import getData, login, setRoomMode, setRoomTemperature, getConsumption

_LOGGER = logging.getLogger(__name__)

class TikoDataUpdateCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, config_entry):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="TikoDataUpdateCoordinator",
            update_interval=timedelta(seconds=30),
            always_update=True,
        )
        self._config_entry = config_entry
        self._credentials = None
        self._data = None
        self._consumption_data = None
        self._apiUrl = (
            self._config_entry.data[CONF_API_URL]
            if CONF_API_URL in self._config_entry.data
            else "https://particuliers-tiko.fr/api/v3/graphql/"
        )

    @property
    def consumption_data(self):
        """Return the consumption data."""
        return self._consumption_data

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(10):
                # Login if not already authenticated or on first run
                if self._credentials is None:
                    self._credentials = await login(
                        self._apiUrl,
                        self._config_entry.data[CONF_USERNAME],
                        self._config_entry.data[CONF_PASSWORD],
                    )
                    if not self._credentials:
                        _LOGGER.error("Failed to authenticate with Tiko API")
                        raise ConfigEntryAuthFailed("Invalid authentication")

                # Get regular data
                newData = await getData(self._apiUrl, self._credentials)
                if newData is None:
                    # Try to re-authenticate once
                    self._credentials = await login(
                        self._apiUrl,
                        self._config_entry.data[CONF_USERNAME],
                        self._config_entry.data[CONF_PASSWORD],
                    )
                    if not self._credentials:
                        raise ConfigEntryAuthFailed("Authentication failed on retry")
                    
                    newData = await getData(self._apiUrl, self._credentials)
                    if newData is None:
                        raise ConfigEntryAuthFailed("Failed to get data after re-authentication")

                self._data = newData

                # Get consumption data only if we have valid property data
                if (self._data and 
                    "data" in self._data and 
                    "properties" in self._data["data"] and 
                    self._data["data"]["properties"]):
                    
                    for prop in self._data["data"]["properties"]:
                        now = datetime.now()
                        start_of_month = datetime(now.year, now.month, 1).timestamp() * 1000
                        current_timestamp = now.timestamp() * 1000
                        
                        try:
                            self._consumption_data = await getConsumption(
                                self._apiUrl,
                                self._credentials,
                                prop["id"],
                                int(start_of_month),
                                int(current_timestamp)
                            )
                        except Exception as consumption_error:
                            _LOGGER.warning("Failed to fetch consumption data: %s", consumption_error)
                            # Don't fail completely if consumption data fails
                            pass

                return self._data

        except ConfigEntryAuthFailed as auth_err:
            raise auth_err
        except Exception as error:
            _LOGGER.error("Error during data update: %s", error)
            raise

    async def set_room_mode(self, propertyId, roomId, mode):
        """Set the room mode."""
        await setRoomMode(
            self._apiUrl,
            self._credentials,
            propertyId,
            roomId,
            mode,
        )
        await self.async_refresh()

    async def set_room_temperature(self, propertyId, roomId, temperature):
        """Set the room temperature."""
        await setRoomTemperature(
            self._apiUrl,
            self._credentials,
            propertyId,
            roomId,
            temperature,
        )
        await self.async_refresh()
