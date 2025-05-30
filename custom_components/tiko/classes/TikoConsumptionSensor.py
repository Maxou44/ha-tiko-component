import logging
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TikoConsumptionSensor(CoordinatorEntity, SensorEntity):
    """An energy consumption sensor for the Tiko integration."""

    def __init__(self, coordinator, property_id, room):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._room = room
        self._property_id = property_id
        self._coordinator = coordinator

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._room['name']} Energy Consumption"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._property_id}_{self._room['id']}_consumption"

    @property
    def native_value(self):
        """Returns the wh of the sensor."""
        if self._coordinator.data is not None:
            for prop in self._coordinator.data["data"]["properties"]:
                if prop["id"] == self._property_id and "fastConsumption" in prop:
                    for room in prop["fastConsumption"]["roomsConsumption"]:
                        if room["id"] == self._room["id"] and room["energyWh"] > 0:
                            return room["energyWh"]
        return None

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
        """Return the device class."""
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        """Return the state class."""
        return SensorStateClass.TOTAL_INCREASING

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfEnergy.WATT_HOUR

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
