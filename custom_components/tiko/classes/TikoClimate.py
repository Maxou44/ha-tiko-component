from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    PRESET_ECO,
    PRESET_NONE,
    PRESET_COMFORT,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN

PRESET_NIGHT = "night"
PRESET_FROST = "frost"


class TikoClimate(CoordinatorEntity, ClimateEntity):
    """A climate for the Tiko integration."""

    def __init__(self, coordinator, property_id, room):
        """Climate initialization."""
        super().__init__(coordinator)
        self._room = room
        self._property_id = property_id
        self._coordinator = coordinator

        self._target_temperature = 19

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
    # Global entity attributes
    # -------------------------------------------

    @property
    def name(self):
        """Returns the name of the climate."""
        return self._room["name"]

    @property
    def unique_id(self):
        """Returns the unique ID of the climate."""
        return f"{self._property_id}_{self._room['id']}_climate"

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
    def supported_features(self):
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
        )

    # -------------------------------------------
    # Climate attributes
    # -------------------------------------------

    @property
    def current_humidity(self):
        """Return the current humidity."""
        room = self._get_room_data()
        return room["humidity"] if room is not None else None

    @property
    def current_temperature(self):
        """Return the current temperature."""
        room = self._get_room_data()
        return room["currentTemperatureDegrees"] if room is not None else None

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return None

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return None

    @property
    def hvac_action(self):
        """Return the current HVAC action."""
        room = self._get_room_data()
        if room is not None:
            if room["status"]["heatingOperating"]:
                return HVACAction.HEATING
            if room["mode"]["disableHeating"]:
                return HVACAction.OFF
            return HVACAction.IDLE
        return None

    @property
    def hvac_mode(self):
        """Return the current operation mode."""
        room = self._get_room_data()
        if room is not None:
            if room["mode"]["disableHeating"]:
                return HVACMode.OFF
            return HVACMode.HEAT
        return None

    # Add HVACMode.AUTO if we have schedule temperatures? See status.temporaryAdjustment

    @property
    def hvac_modes(self):
        """Return the list of available HVAC operation modes."""
        return [HVACMode.OFF, HVACMode.HEAT]

    @property
    def max_humidity(self):
        """Return the maximum humidity."""
        return 100

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 40

    @property
    def min_humidity(self):
        """Return the minimum humidity."""
        return 1

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 1

    @property
    def precision(self):
        """Return the precision of the temperature."""
        return 0.1

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        room = self._get_room_data()
        if room is not None:
            if room["mode"]["disableHeating"]:
                return PRESET_NONE
            if room["mode"]["comfort"]:
                return PRESET_COMFORT
            if room["mode"]["absence"]:
                return PRESET_ECO
            if room["mode"]["sleep"]:
                return PRESET_NIGHT
            if room["mode"]["frost"]:
                return PRESET_FROST
        return PRESET_NONE

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return [PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_NIGHT, PRESET_FROST]

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return None  # Not supported by Tiko

    @property
    def swing_modes(self):
        """Return the swing modes."""
        return None  # Not supported by Tiko

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return None  # Not supported by Tiko

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        room = self._get_room_data()
        return room["targetTemperatureDegrees"] if room is not None else None

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return None  # Not supported by Tiko

    @property
    def target_temperature_low(self):
        """Return the lowerbound target temperature we try to reach."""
        return None  # Not supported by Tiko

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 0.1

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    # -------------------------------------------
    # Climate methods
    # -------------------------------------------

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        room = self._get_room_data()

        if self._room is not None:
            # Disable it
            if hvac_mode == HVACMode.OFF:
                await self._coordinator.set_room_mode(
                    self._property_id, room["id"], "disableHeating"
                )

            # Enable it
            if hvac_mode == HVACMode.HEAT:
                await self._coordinator.set_room_mode(
                    self._property_id, room["id"], None
                )

    async def async_turn_on(self):
        """Turn the entity on."""
        return self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self):
        """Turn the entity off."""
        return self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        value = False

        if preset_mode == PRESET_COMFORT:
            value = "comfort"
        elif preset_mode == PRESET_ECO:
            value = "absence"
        elif preset_mode == PRESET_NIGHT:
            value = "sleep"
        elif preset_mode == PRESET_FROST:
            value = "frost"

        await self._coordinator.set_room_mode(
            self._property_id, self._room["id"], value
        )

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            if kwargs[ATTR_TEMPERATURE] > 0:
                self._target_temperature = kwargs[ATTR_TEMPERATURE]
            await self._coordinator.set_room_temperature(
                self._property_id,
                self._room["id"],
                kwargs[ATTR_TEMPERATURE],
            )

    # -------------------------------------------
    # Coordinator refresh
    # -------------------------------------------

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
