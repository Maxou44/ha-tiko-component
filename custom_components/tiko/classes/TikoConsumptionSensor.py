import logging
from datetime import datetime, timedelta
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
        self._last_valid_value = None
        self._last_update = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._room['name']} Energy Consumption"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._property_id}_{self._room['id']}_consumption"

    def _get_consumption_value(self):
        """Get consumption value with validation."""
        if self._coordinator.consumption_data is not None:
            consumption_data = self._coordinator.consumption_data
            if ("data" in consumption_data 
                and "property" in consumption_data["data"]
                and consumption_data["data"]["property"] is not None):
                
                property_data = consumption_data["data"]["property"]
                if ("fastConsumption" in property_data 
                    and property_data["fastConsumption"] is not None
                    and "roomsConsumption" in property_data["fastConsumption"]):
                    
                    for room in property_data["fastConsumption"]["roomsConsumption"]:
                        if str(room["id"]) == str(self._room["id"]):
                            if "energyKwh" in room and room["energyKwh"] is not None:
                                return room["energyKwh"]
        return None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        current_value = self._get_consumption_value()
        
        if current_value is not None:
            # Only update if the value is greater than 0 
            # or if we don't have a last valid value
            if current_value > 0 or self._last_valid_value is None:
                self._last_valid_value = current_value
                self._last_update = datetime.now()
                return current_value
            
            # If the current value is 0 but we have a recent valid value
            # return the last valid value instead
            if (self._last_valid_value is not None 
                and self._last_update is not None 
                and datetime.now() - self._last_update < timedelta(minutes=5)):
                return self._last_valid_value
            
            # If the last valid value is too old, accept the new value
            self._last_valid_value = current_value
            self._last_update = datetime.now()
            return current_value
            
        # Return last valid value if we have one and it's not too old
        if (self._last_valid_value is not None 
            and self._last_update is not None 
            and datetime.now() - self._last_update < timedelta(minutes=5)):
            return self._last_valid_value
            
        return current_value

    @property
    def device_info(self):
        """Return device information."""
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
        return UnitOfEnergy.KILO_WATT_HOUR

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()