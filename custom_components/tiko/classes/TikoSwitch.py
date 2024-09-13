import logging

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.switch import (
    SwitchEntity,
)

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TikoSwitch(CoordinatorEntity, SwitchEntity):
    """A switch on Tiko equipment."""

    def __init__(self, coordinator, property_id, room, type):
        """Switch initialization."""
        super().__init__(coordinator)
        self._room = room
        self._type = type
        self._property_id = property_id
        self._coordinator = coordinator
        _LOGGER.error("DEVICE SWITCH DBG: %s - %s - %s", room, type, property_id)


    @property
    def name(self):
        """Returns the name of the switch."""
        if self._type == "absence":
            return f"{'General' if self._room is None else self._room['name']} Absence mode"
        if self._type == "boost":
            return (
                f"{'General' if self._room is None else self._room['name']} Boost mode"
            )
        if self._type == "frost":
            return (
                f"{'General' if self._room is None else self._room['name']} Frost mode"
            )
        if self._type == "disable_heating":
            return f"{'General' if self._room is None else self._room['name']} Disable heating mode"
        return None

    @property
    def is_on(self):
        """Returns the state of the switch."""
        if self._coordinator.data is not None:
            propertyMode = None
            roomMode = None

            for prop in self._coordinator.data["data"]["properties"]:
                if prop["id"] == self._property_id:
                    propertyMode = prop["mode"]
                    for room in prop["rooms"]:
                        if self._room is not None and room["id"] == self._room["id"]:
                            roomMode = room["mode"]

            mode = roomMode if roomMode is not None else propertyMode

            if mode == "boost":
                return mode["boost"]
            if mode == "absence":
                return mode["absence"]
            if mode == "disable_heating":
                return mode["disableHeating"]
            if mode == "frost":
                return mode["frost"]

        return False

    @property
    def unique_id(self):
        """Returns the unique ID of the sensor."""
        if self._room is None:
            return f"{self._property_id}_{self._type}"
        return f"{self._property_id}_{self._room["id"]}_{self._type}"

    @property
    def device_info(self):
        """Returns switch information."""
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

    async def async_turn_on(self):
        """When the switch is turned on."""
        # await set_radiator_state(self._room_id, self._radiator_id, True)
        self.async_write_ha_state()

    async def async_turn_off(self):
        """When the switch is turned off."""
        # await set_radiator_state(self._room_id, self._radiator_id, False)
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data
        # _LOGGER.error("SENSOR: %s", data)
