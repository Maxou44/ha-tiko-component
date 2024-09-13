import logging

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity

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
        _LOGGER.error("DEVICE DBG: %s - %s - %s", room, type, property_id)

    @property
    def name(self):
        """Returns the name of the sensor."""
        if self._type == "temperature_target":
            return f"{self._room["name"]} Target temperature"
        if self._type == "temperature_current":
            return f"{self._room["name"]} Current temperature"
        return None

    @property
    def state(self):
        """Returns the temperature of the sensor."""
        if self._coordinator.data is not None:
            for prop in self._coordinator.data["data"]["properties"]:
                if prop["id"] == self._property_id:
                    for room in prop["rooms"]:
                        if room["id"] == self._room["id"]:
                            if self._type == "temperature_target":
                                return room["targetTemperatureDegrees"]
                            if self._type == "temperature_current":
                                return room["currentTemperatureDegrees"]
        return None

    @property
    def unique_id(self):
        """Returns the unique ID of the sensor."""
        if self._type == "temperature_target":
            _LOGGER.error(
                "SENSOR_TEMP_ID: %s",
                f"{self._property_id}_{self._room["id"]}_temperature_target",
            )
            return f"{self._property_id}_{self._room["id"]}_temperature_target"
        if self._type == "temperature_current":
            _LOGGER.error(
                "SENSOR_TEMP_ID: %s",
                f"{self._property_id}_{self._room["id"]}_temperature_current",
            )
            return f"{self._property_id}_{self._room["id"]}_temperature_current"
        return None

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
        return "temperature"

    @property
    def unit_of_measurement(self):
        """Returns the unit of measurement that is being used."""
        return "°C"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data
        # _LOGGER.error("SENSOR: %s", data)

    async def async_update(self):
        self.async_write_ha_state()
