import logging
from .const import DOMAIN
from .classes.TikoDataUpdateCoordinator import TikoDataUpdateCoordinator
from .classes.TikoConsumptionDataUpdateCoordinator import (
    TikoConsumptionDataUpdateCoordinator,
)
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(seconds=30)

PLATFORMS = ["sensor", "climate"]


async def async_setup_entry(hass, config_entry):
    """Setup Tiko component"""
    hass.data.setdefault(DOMAIN, {})

    # Get entry id
    entry_id = config_entry.entry_id
    if not isinstance(entry_id, str):
        entry_id = str(entry_id)

    # Data coordinator setup
    coordinator = TikoDataUpdateCoordinator(hass, config_entry)
    consumptionCoordinator = TikoConsumptionDataUpdateCoordinator(hass, config_entry)

    # Try to get initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Error getting initial data: %s", err)
        return False

    # Store coordinators
    hass.data[DOMAIN][entry_id] = [coordinator, consumptionCoordinator]

    # Init entities
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Indicate that the initialization was successful
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""

    # Get entry id
    entry_id = config_entry.entry_id
    if not isinstance(entry_id, str):
        entry_id = str(entry_id)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    # Clean HASS object
    if unload_ok and entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry_id)

    return unload_ok
