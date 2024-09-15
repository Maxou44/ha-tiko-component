import logging

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TikoTemperatureSensor(CoordinatorEntity, SensorEntity):
    """A temperature sensor for the Tiko integration."""

    def __init__(self, coordinator, property_id, room, type=None):
        """Sensor initialization."""
        super().__init__(coordinator)
        self._room = room
        self._type = type
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

    # -------------------------------------------
    # Sensor properties
    # -------------------------------------------

    @property
    def name(self):
        """Returns the name of the sensor."""
        if self._type == "temperature_target":
            return f"{self._room["name"]} Target temperature"
        if self._type == "temperature_current":
            return f"{self._room["name"]} Current temperature"
        return None

    @property
    def native_value(self):
        """Returns the temperature of the sensor."""
        room = self._get_room_data()

        if self._type == "temperature_target":
            if (
                room["mode"]["disableHeating"] is not True
                or room["targetTemperatureDegrees"] > 0
            ):
                return room["targetTemperatureDegrees"]
        if self._type == "temperature_current":
            return room["currentTemperatureDegrees"]
        return None

    @property
    def unique_id(self):
        """Returns the unique ID of the sensor."""
        if self._type == "temperature_target":
            return f"{self._property_id}_{self._room["id"]}_temperature_target"
        if self._type == "temperature_current":
            return f"{self._property_id}_{self._room["id"]}_temperature_current"
        return None

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
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self):
        """Returns the unit of measurement that is being used."""
        return UnitOfTemperature.CELSIUS

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
