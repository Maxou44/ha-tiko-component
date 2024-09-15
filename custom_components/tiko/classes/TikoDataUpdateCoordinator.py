from datetime import timedelta
import logging

import async_timeout

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import getData, login, setRoomMode, setRoomTemperature

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

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with async_timeout.timeout(10):
            if self._credentials is None:
                self._credentials = await login(
                    self._config_entry.data[CONF_USERNAME],
                    self._config_entry.data[CONF_PASSWORD],
                )

            newData = await getData(self._credentials)
            self.async_set_updated_data(newData)
            if newData is not None:
                self._data = newData

            return self._data

    async def set_room_mode(self, propertyId, roomId, mode):
        """Set the room mode."""
        await setRoomMode(self._credentials, propertyId, roomId, mode)
        await self.async_refresh()

    async def set_room_temperature(self, propertyId, roomId, temperature):
        """Set the room temperature."""
        await setRoomTemperature(self._credentials, propertyId, roomId, temperature)
        await self.async_refresh()
