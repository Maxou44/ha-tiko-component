import logging
from .classes.TikoHumiditySensor import TikoHumiditySensor
from .classes.TikoTemperatureSensor import TikoTemperatureSensor
from .classes.TikoBatterySensor import TikoBatterySensor
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Tiko sensors based on a config entry."""

    # Get Tiko data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    tiko_data = coordinator.data
    # _LOGGER.error("tiko_data: %s", tiko_data)

    # For each property
    entities = []
    for prop in tiko_data["data"]["properties"]:
        property_id = prop["id"]

        for room in prop["rooms"]:
            # Humidity sensor
            entities.append(
                TikoHumiditySensor(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                )
            )

            # Current temperature sensor
            entities.append(
                TikoTemperatureSensor(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                    type="temperature_current",
                )
            )

            # Target temperature sensor
            entities.append(
                TikoTemperatureSensor(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                    type="temperature_target",
                )
            )

            # Battery sensor
            entities.append(
                TikoBatterySensor(
                    coordinator=coordinator,
                    property_id=property_id,
                    room=room,
                )
            )

    # Push sensors to HA
    async_add_entities(entities, update_before_add=True)
