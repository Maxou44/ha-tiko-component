import logging
from .classes.TikoClimate import TikoClimate
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Tiko climate based on a config entry."""

    # Get Tiko data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    tiko_data = coordinator.data

    # Check if we have valid data
    if not tiko_data or "data" not in tiko_data or "properties" not in tiko_data["data"]:
        _LOGGER.warning("No Tiko data available during climate setup, waiting for first update")
        return

    # For each property
    entities = []
    for prop in tiko_data["data"]["properties"]:
        property_id = prop["id"]

        for room in prop["rooms"]:
            # Climate
            entities.append(
                TikoClimate(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                )
            )

    # Push sensors to HA
    if entities:
        async_add_entities(entities, update_before_add=True)