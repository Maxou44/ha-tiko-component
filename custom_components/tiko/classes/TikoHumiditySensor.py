import logging

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.const import PERCENTAGE

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
    def native_value(self):
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
            return f"{self._property_id}_humidity"
        return f"{self._property_id}_{self._room["id"]}_humidity"

    @property
    def device_info(self):
        """Returns device information."""
        return {
            "identifiers": {(DOMAIN, self._property_id)}
            if self._room is None
            else {(DOMAIN, self._room["id"])},
            "name": "General" if self._room is None else self._room["name"],
            "manufacturer": "Tiko",
            "model": "Tiko Equipment",
            "sw_version": "1.0",
        }

    @property
    def device_class(self):
        """Returns the type of value that is being measured."""
        return SensorDeviceClass.HUMIDITY

    @property
    def native_unit_of_measurement(self):
        """Returns the unit of measurement that is being used."""
        return PERCENTAGE

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


"""

# par piece :
"heaters": 1,
"sensors": 1,

"status": {
                        "disconnected": false,
                        "heaterDisconnected": false,
                        "heatingOperating": true, // en cours de chauffe
                        "sensorBatteryLow": false,
                        "sensorDisconnected": false,
                        "temporaryAdjustment": false,
                        "__typename": "RoomStatusType"
                    },
"""

"""
detect le <= 0 pour la temperature


min officiel 5°C
max 40°C

"""
