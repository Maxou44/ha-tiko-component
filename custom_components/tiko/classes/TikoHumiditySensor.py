import logging

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TikoHumiditySensor(CoordinatorEntity, SensorEntity):
    """A humidity sensor for the Tiko integration."""

    def __init__(self, coordinator, property_id, room):
        """Sensor initialization."""
        super().__init__(coordinator)
        self._room = room
        self._property_id = property_id
        self._coordinator = coordinator
        _LOGGER.error("DEVICE SENSOR HUMIDITY : %s - %s", room, property_id)

    @property
    def name(self):
        """Returns the name of the sensor."""
        return f"{self._room["name"]} Current Humidity"

    @property
    def state(self):
        """Returns the humidity of the sensor."""
        if self._coordinator.data is not None:
            for prop in self._coordinator.data["data"]["properties"]:
                if prop["id"] == self._property_id:
                    for room in prop["rooms"]:
                        if room["id"] == self._room["id"]:
                            return room["humidity"]
        return None

    @property
    def unique_id(self):
        """Returns the unique ID of the sensor."""
        if self._room is None:
            _LOGGER.error("SENSOR_ID: %s", f"{self._property_id}_humidity")
            return f"{self._property_id}_humidity"
        _LOGGER.error(
            "SENSOR_ID: %s", f"{self._property_id}_{self._room["id"]}_humidity"
        )
        return f"{self._property_id}_{self._room["id"]}_humidity"

    @property
    def device_info(self):
        """Returns device information."""
        if self._room is None:
            return {
                "identifiers": {(DOMAIN, self._property_id)},
                "name": "General",
                "manufacturer": "Tiko",
                "model": "Tiko Equipment",
                "sw_version": "1.0",
            }
        return {
            "identifiers": {(DOMAIN, self._room["id"])},
            "name": self._room["name"],
            "manufacturer": "Tiko",
            "model": "Tiko Equipment",
            "sw_version": "1.0",
        }

    @property
    def device_class(self):
        """Returns the type of value that is being measured."""
        return "humidity"

    @property
    def unit_of_measurement(self):
        """Returns the unit of measurement that is being used."""
        return "%"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data
        # _LOGGER.error("SENSOR: %s", data)

    async def async_update(self):
        self.async_write_ha_state()
