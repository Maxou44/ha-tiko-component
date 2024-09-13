import logging
from .classes.TikoSwitch import TikoSwitch
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Tiko switches based on a config entry."""

    # Get Tiko data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    tiko_data = coordinator.data
    # _LOGGER.error("tiko_data: %s", tiko_data)

    # For each property
    entities = []
    for prop in tiko_data["data"]["properties"]:
        property_id = prop["id"]

        # Boost mode
        entities.append(
            TikoSwitch(
                coordinator=coordinator,
                property_id=property_id,
                room=None,
                type="boost",
            )
        )

        # Frost mode
        entities.append(
            TikoSwitch(
                coordinator=coordinator,
                property_id=property_id,
                room=None,
                type="frost",
            )
        )

        # Absence mode
        entities.append(
            TikoSwitch(
                coordinator=coordinator,
                property_id=property_id,
                room=None,
                type="absence",
            )
        )

        # Disable heating mode
        entities.append(
            TikoSwitch(
                coordinator=coordinator,
                property_id=property_id,
                room=None,
                type="disable_heating",
            )
        )

        for room in prop["rooms"]:
            # Boost mode
            entities.append(
                TikoSwitch(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                    type="boost",
                )
            )

            # Frost mode
            entities.append(
                TikoSwitch(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                    type="frost",
                )
            )

            # Absence mode
            entities.append(
                TikoSwitch(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                    type="absence",
                )
            )

            # Disable heating mode
            entities.append(
                TikoSwitch(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                    type="disable_heating",
                )
            )

    # Push switches to HA
    async_add_entities(entities, update_before_add=True)
