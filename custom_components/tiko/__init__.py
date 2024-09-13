import logging
from .const import DOMAIN
from .classes.TikoDataUpdateCoordinator import TikoDataUpdateCoordinator
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass, config_entry):
    """Configure le component Tiko via une entrée de configuration."""
    hass.data.setdefault(DOMAIN, {})

    # Get entry id
    entry_id = config_entry.entry_id
    if not isinstance(entry_id, str):
        entry_id = str(entry_id)

    # Data coordinator setup
    coordinator = TikoDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry_id] = coordinator

    # Init entities
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(
            config_entry, ["sensor", "switch"]
        )
    )

    # Indicate that the initialization was successful
    return True


async def async_unload_entry(hass, config_entry):
    entry_id = config_entry.entry_id

    # Nettoyer les données spécifiques à cette entrée
    # if entry_id in hass.data[DOMAIN]:
    #    hass.data[DOMAIN].pop(entry_id)
