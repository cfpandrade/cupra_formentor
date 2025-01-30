"""Button integration for Cupra We Connect."""
from __future__ import annotations

from weconnect_cupra import weconnect_cupra

from homeassistant.components.button import ButtonEntity

from . import get_object_value, start_stop_charging, set_climatisation, set_ac_charging_speed
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up buttons for Cupra We Connect."""
    we_connect: weconnect_cupra.WeConnect = hass.data[DOMAIN][config_entry.entry_id]
    vehicles = hass.data[DOMAIN][config_entry.entry_id + "_vehicles"]

    entities = [
        CupraStartClimateButton(vehicle, we_connect),
        CupraStopClimateButton(vehicle, we_connect),
        CupraStartChargingButton(vehicle, we_connect),
        CupraStopChargingButton(vehicle, we_connect),
        CupraToggleACChargeSpeed(vehicle, we_connect)
        for vehicle in vehicles
    ]
    
    async_add_entities(entities)

class CupraStartClimateButton(ButtonEntity):
    """Button for starting climate."""
    def __init__(self, vehicle, we_connect) -> None:
        self._attr_name = f"{vehicle.nickname} Start Climate"
        self._attr_unique_id = f"{vehicle.vin}-start_climate"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        set_climatisation(self._vehicle.vin.value, self._we_connect, "start", 0)

class CupraStopClimateButton(ButtonEntity):
    """Button for stopping climate."""
    def __init__(self, vehicle, we_connect) -> None:
        self._attr_name = f"{vehicle.nickname} Stop Climate"
        self._attr_unique_id = f"{vehicle.vin}-stop_climate"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        set_climatisation(self._vehicle.vin.value, self._we_connect, "stop", 0)

class CupraStartChargingButton(ButtonEntity):
    """Button for starting charging."""
    def __init__(self, vehicle, we_connect) -> None:
        self._attr_name = f"{vehicle.nickname} Start Charging"
        self._attr_unique_id = f"{vehicle.vin}-start_charging"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        start_stop_charging(self._vehicle.vin.value, self._we_connect, "start")

class CupraStopChargingButton(ButtonEntity):
    """Button for stopping charging."""
    def __init__(self, vehicle, we_connect) -> None:
        self._attr_name = f"{vehicle.nickname} Stop Charging"
        self._attr_unique_id = f"{vehicle.vin}-stop_charging"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        start_stop_charging(self._vehicle.vin.value, self._we_connect, "stop")

class CupraToggleACChargeSpeed(ButtonEntity):
    """Button for toggling AC charge speed."""
    def __init__(self, vehicle, we_connect: weconnect_cupra.WeConnect) -> None:
        self._attr_name = f"{vehicle.nickname} Toggle AC Charge Speed"
        self._attr_unique_id = f"{vehicle.vin}-toggle_ac_charge_speed"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        current_state = get_object_value(
            self._vehicle.domains["charging"]["chargingSettings"].maxChargeCurrentAC
        )
        new_state = "reduced" if current_state == "maximum" else "maximum"
        set_ac_charging_speed(self._vehicle.vin.value, self._we_connect, new_state)
