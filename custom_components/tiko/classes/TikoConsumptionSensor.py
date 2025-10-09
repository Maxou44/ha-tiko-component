"""Tiko Consumption Sensor - Improved version."""
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
        self._attr_has_entity_name = True

    # -------------------------------------------
    # Sensor properties
    # -------------------------------------------

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
        """Return the energy consumption in Wh."""
        if self._coordinator.data is None:
            return None

        try:
            data = self._coordinator.data

            # Check data structure
            if "data" not in data or "properties" not in data["data"]:
                _LOGGER.debug("Invalid data structure in consumption coordinator")
                return None

            # Find the property
            for prop in data["data"]["properties"]:
                if prop["id"] != self._property_id:
                    continue

                # Check if fastConsumption exists
                if "fastConsumption" not in prop:
                    _LOGGER.debug("No fastConsumption data for property %s", self._property_id)
                    return None

                fast_consumption = prop["fastConsumption"]

                # Check if roomsConsumption exists
                if "roomsConsumption" not in fast_consumption:
                    _LOGGER.debug("No roomsConsumption data")
                    return None

                # Find the room
                for room in fast_consumption["roomsConsumption"]:
                    if room["id"] == self._room["id"]:
                        energy_wh = room.get("energyWh")

                        # Only return positive values
                        if energy_wh is not None and energy_wh > 0:
                            return energy_wh

                        _LOGGER.debug(
                            "Room %s has no consumption data or value is 0",
                            self._room["name"]
                        )
                        return None

            _LOGGER.debug("Room %s not found in consumption data", self._room["name"])
            return None

        except Exception as e:
            _LOGGER.error("Error getting consumption value: %s", e)
            return None

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if self._coordinator.data is None:
            return {}

        try:
            data = self._coordinator.data

            if "data" not in data or "properties" not in data["data"]:
                return {}

            for prop in data["data"]["properties"]:
                if prop["id"] != self._property_id:
                    continue

                if "fastConsumption" not in prop:
                    return {}

                fast_consumption = prop["fastConsumption"]

                if "roomsConsumption" not in fast_consumption:
                    return {}

                for room in fast_consumption["roomsConsumption"]:
                    if room["id"] == self._room["id"]:
                        energy_kwh = room.get("energyKwh")
                        energy_wh = room.get("energyWh")

                        attrs = {}

                        if energy_kwh is not None:
                            attrs["energy_kwh"] = round(energy_kwh, 3)

                        if energy_wh is not None:
                            attrs["energy_wh"] = energy_wh

                        return attrs

            return {}

        except Exception as e:
            _LOGGER.error("Error getting extra attributes: %s", e)
            return {}

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
        return UnitOfEnergy.WATT_HOUR

    @property
    def available(self):
        """Return if entity is available."""
        return self._coordinator.last_update_success

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()