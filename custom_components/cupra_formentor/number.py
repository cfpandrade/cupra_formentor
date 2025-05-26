"""Number platform for Cupra Formentor integration."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CupraFormentorBaseEntity, get_object_value, set_climatisation, set_target_soc
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities for Cupra Formentor."""
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    entities = []

    for index, vehicle in enumerate(coordinator.data):
        # Only add target SOC if charging domain exists
        if hasattr(vehicle.domains, 'charging') and \
           hasattr(vehicle.domains.charging, 'chargingSettings'):
            entities.append(CupraTargetSoCNumber(we_connect, coordinator, index))
        
        # Only add target temperature if climatisation domain exists
        if hasattr(vehicle.domains, 'climatisation') and \
           hasattr(vehicle.domains.climatisation, 'climatisationSettings'):
            entities.append(CupraTargetClimateNumber(we_connect, coordinator, index))
    
    if entities:
        async_add_entities(entities)


class CupraTargetSoCNumber(CupraFormentorBaseEntity, NumberEntity):
    """Representation of a Target State of Charge entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery-charging"

    def __init__(self, we_connect, coordinator, index) -> None:
        """Initialize entity."""
        super().__init__(we_connect, coordinator, index)
        self._attr_name = f"{self.data.nickname.value} SOC Objetivo"
        self._attr_unique_id = f"{self.data.vin.value}_target_state_of_charge"
        self._attr_native_min_value = 10
        self._attr_native_max_value = 100
        self._attr_native_step = 10

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        try:
            return int(get_object_value(
                self.data.domains.charging.chargingSettings.targetSOC_pct
            ))
        except Exception as e:
            _LOGGER.debug("Error getting target SOC: %s", e)
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if value >= 10:
            await self.hass.async_add_executor_job(
                set_target_soc,
                self.data.vin.value,
                self.we_connect,
                int(value)
            )


class CupraTargetClimateNumber(CupraFormentorBaseEntity, NumberEntity):
    """Representation of a Target Climate Temperature entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer"

    def __init__(self, we_connect, coordinator, index) -> None:
        """Initialize entity."""
        super().__init__(we_connect, coordinator, index)
        self._attr_name = f"{self.data.nickname.value} Temperatura Objetivo"
        self._attr_unique_id = f"{self.data.vin.value}_target_climate_temperature"
        self._attr_native_min_value = 10
        self._attr_native_max_value = 30
        self._attr_native_step = 0.5

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        try:
            return float(get_object_value(
                self.data.domains.climatisation.climatisationSettings.targetTemperature_C
            ))
        except Exception as e:
            _LOGGER.debug("Error getting target temperature: %s", e)
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if value >= 10:
            await self.hass.async_add_executor_job(
                set_climatisation,
                self.data.vin.value,
                self.we_connect,
                "none",
                float(value)
            )