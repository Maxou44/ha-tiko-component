import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TikoBatterySensor(CoordinatorEntity, BinarySensorEntity):
    """A battery binary sensor for the Tiko integration."""

    def __init__(self, coordinator, property_id, room):
        """Sensor initialization."""
        super().__init__(coordinator)
        self._room = room
        self._property_id = property_id
        self._coordinator = coordinator

    # -------------------------------------------
    # Helpers
    # -------------------------------------------

    def _get_room_data(self):
        if self._coordinator.data is not None:
            for prop in self._coordinator.data["data"]["properties"]:
                if prop["id"] == self._property_id:
                    for room in prop["rooms"]:
                        if room["id"] == self._room["id"]:
                            return room
        return None


    @property
    def name(self):
        """Returns the name of the sensor."""
        return f"{self._room["name"]} Battery"

    @property
    def is_on(self):
        """Return True if the battery is low, False otherwise."""
        room = self._get_room_data()
        if room is not None:
           return room["status"]["sensorBatteryLow"]
        return False

    @property
    def unique_id(self):
        """Returns the unique ID of the battery sensor."""
        return f"{self._property_id}_{self._room["id"]}_battery"

    @property
    def device_info(self):
        """Returns device information."""
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
        return BinarySensorDeviceClass.BATTERY

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
