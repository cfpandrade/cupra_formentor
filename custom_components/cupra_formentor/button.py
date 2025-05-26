"""Button platform for Cupra Formentor integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import get_object_value, start_stop_charging, set_climatisation, set_ac_charging_speed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up buttons for Cupra Formentor."""
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    entities = []

    for index, vehicle in enumerate(coordinator.data):
        # Only add charging buttons if charging domain exists
        if hasattr(vehicle.domains, 'charging'):
            entities.extend([
                CupraStartChargingButton(vehicle, we_connect),
                CupraStopChargingButton(vehicle, we_connect),
                CupraToggleACChargeSpeed(vehicle, we_connect),
            ])
        
        # Only add climate buttons if climatisation domain exists
        if hasattr(vehicle.domains, 'climatisation'):
            entities.extend([
                CupraStartClimateButton(vehicle, we_connect),
                CupraStopClimateButton(vehicle, we_connect),
            ])
    
    if entities:
        async_add_entities(entities)


class CupraStartClimateButton(ButtonEntity):
    """Button for starting climate."""
    
    def __init__(self, vehicle, we_connect) -> None:
        """Initialize button."""
        self._attr_name = f"{vehicle.nickname.value} Iniciar Climatización"
        self._attr_unique_id = f"{vehicle.vin.value}_start_climate"
        self._we_connect = we_connect
        self._vehicle = vehicle

    async def async_press(self) -> None:
        """Handle button press."""
        await self.hass.async_add_executor_job(
            set_climatisation, 
            self._vehicle.vin.value, 
            self._we_connect, 
            "start", 
            0
        )


class CupraStopClimateButton(ButtonEntity):
    """Button for stopping climate."""
    
    def __init__(self, vehicle, we_connect) -> None:
        """Initialize button."""
        self._attr_name = f"{vehicle.nickname.value} Detener Climatización"
        self._attr_unique_id = f"{vehicle.vin.value}_stop_climate"
        self._we_connect = we_connect
        self._vehicle = vehicle

    async def async_press(self) -> None:
        """Handle button press."""
        await self.hass.async_add_executor_job(
            set_climatisation,
            self._vehicle.vin.value,
            self._we_connect,
            "stop",
            0
        )


class CupraStartChargingButton(ButtonEntity):
    """Button for starting charging."""
    
    def __init__(self, vehicle, we_connect) -> None:
        """Initialize button."""
        self._attr_name = f"{vehicle.nickname.value} Iniciar Carga"
        self._attr_unique_id = f"{vehicle.vin.value}_start_charging"
        self._we_connect = we_connect
        self._vehicle = vehicle

    async def async_press(self) -> None:
        """Handle button press."""
        await self.hass.async_add_executor_job(
            start_stop_charging,
            self._vehicle.vin.value,
            self._we_connect,
            "start"
        )


class CupraStopChargingButton(ButtonEntity):
    """Button for stopping charging."""
    
    def __init__(self, vehicle, we_connect) -> None:
        """Initialize button."""
        self._attr_name = f"{vehicle.nickname.value} Detener Carga"
        self._attr_unique_id = f"{vehicle.vin.value}_stop_charging"
        self._we_connect = we_connect
        self._vehicle = vehicle

    async def async_press(self) -> None:
        """Handle button press."""
        await self.hass.async_add_executor_job(
            start_stop_charging,
            self._vehicle.vin.value,
            self._we_connect,
            "stop"
        )


class CupraToggleACChargeSpeed(ButtonEntity):
    """Button for toggling AC charge speed."""
    
    def __init__(self, vehicle, we_connect) -> None:
        """Initialize button."""
        self._attr_name = f"{vehicle.nickname.value} Cambiar Velocidad Carga AC"
        self._attr_unique_id = f"{vehicle.vin.value}_toggle_ac_charge_speed"
        self._we_connect = we_connect
        self._vehicle = vehicle

    async def async_press(self) -> None:
        """Handle button press."""
        try:
            if hasattr(self._vehicle.domains, 'charging') and \
               hasattr(self._vehicle.domains.charging, 'chargingSettings'):
                current_state = get_object_value(
                    self._vehicle.domains.charging.chargingSettings.maxChargeCurrentAC
                )
                new_state = "reduced" if current_state == "maximum" else "maximum"
                
                await self.hass.async_add_executor_job(
                    set_ac_charging_speed,
                    self._vehicle.vin.value,
                    self._we_connect,
                    new_state
                )
        except Exception as e:
            _LOGGER.error("Error toggling AC charge speed: %s", e)