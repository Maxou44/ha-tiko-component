from datetime import timedelta
import logging

import async_timeout

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from ..const import CONF_API_URL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import getConsumptionData, login

_LOGGER = logging.getLogger(__name__)


class TikoConsumptionDataUpdateCoordinator(DataUpdateCoordinator):
    """Tiko consumption data coordinator."""

    def __init__(self, hass, config_entry):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="TikoConsumptionDataUpdateCoordinator",
            update_interval=timedelta(seconds=300),
            always_update=True,
        )
        self._config_entry = config_entry
        self._credentials = None
        self._data = None
        self._apiUrl = self._config_entry.data.get(CONF_API_URL, None)

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with async_timeout.timeout(10):
            if self._credentials is None:
                self._credentials = await login(
                    self._apiUrl,
                    self._config_entry.data[CONF_USERNAME],
                    self._config_entry.data[CONF_PASSWORD],
                )

            newData = await getConsumptionData(self._apiUrl, self._credentials)
            self.async_set_updated_data(newData)
            if newData is not None:
                self._data = newData

            return self._data
