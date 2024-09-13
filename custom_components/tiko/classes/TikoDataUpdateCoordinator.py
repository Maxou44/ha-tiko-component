from datetime import timedelta
import logging

import async_timeout

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import getData, login

_LOGGER = logging.getLogger(__name__)


class TikoDataUpdateCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, config_entry):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="TikoDataUpdateCoordinator",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True,
        )
        self._config_entry = config_entry
        self._credentials = None
        self._data = None

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """

    # self._data = await self.my_api.get_device()

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        # try:
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        async with async_timeout.timeout(15):
            # Grab active context variables to limit data required to be fetched from API
            # Note: using context is not required if there is no need or ability to limit
            # data retrieved from API.
            # listening_idx = set(self.async_contexts())
            # return await self.my_api.fetch_data(listening_idx)

            if self._credentials is None:
                self._credentials = await login(
                    self._config_entry.data[CONF_USERNAME],
                    self._config_entry.data[CONF_PASSWORD],
                )

            _LOGGER.error("TOKENS: %s", self._credentials)

            newData = await getData(self._credentials)
            if newData is not None:
                self._data = newData

            return self._data

        # except ApiAuthError as err:
        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #   raise ConfigEntryAuthFailed from err

    # except Error as err:
    #   raise UpdateFailed(f"Error communicating with API: {err}")
