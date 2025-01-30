"""Number entity integration for Cupra We Connect."""
from __future__ import annotations

from weconnect_cupra import weconnect_cupra

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import CupraWeConnectEntity, get_object_value, set_climatisation, set_target_soc
from .const import DOMAIN
from homeassistant.const import UnitOfTemperature

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up number entities for Cupra We Connect."""
    we_connect: weconnect_cupra.WeConnect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    await coordinator.async_config_entry_first_refresh()

    entities = [
        CupraTargetSoCNumber(we_connect, coordinator, index),
        CupraTargetClimateNumber(we_connect, coordinator, index)
        for index, vehicle in enumerate(coordinator.data)
    ]
    
    if entities:
        async_add_entities(entities)

class CupraTargetSoCNumber(CupraWeConnectEntity, NumberEntity):
    """Representation of a Target State of Charge entity."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, we_connect: weconnect_cupra.WeConnect, coordinator: DataUpdateCoordinator, index: int) -> None:
        super().__init__(we_connect, coordinator, index)
        self._coordinator = coordinator
        self._attr_name = f"{self.data.nickname} Target State Of Charge"
        self._attr_unique_id = f"{self.data.vin}-target_state_of_charge"
        self._we_connect = we_connect
        self._attr_native_min_value = 10
        self._attr_native_max_value = 100
        self._attr_native_step = 10

    @property
    def native_value(self) -> float | None:
        return int(get_object_value(self.data.domains["charging"]["chargingSettings"].targetSOC_pct.value))

    async def async_set_native_value(self, value: float) -> None:
        if value > 10:
            await self.hass.async_add_executor_job(set_target_soc, self.data.vin.value, self._we_connect, value)

class CupraTargetClimateNumber(CupraWeConnectEntity, NumberEntity):
    """Representation of a Target Climate Temperature entity."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, we_connect: weconnect_cupra.WeConnect, coordinator: DataUpdateCoordinator, index: int) -> None:
        super().__init__(we_connect, coordinator, index)
        self._coordinator = coordinator
        self._attr_name = f"{self.data.nickname} Target Climate Temperature"
        self._attr_unique_id = f"{self.data.vin}-target_climate_temperature"
        self._we_connect = we_connect
        self._attr_native_min_value = 10
        self._attr_native_max_value = 30
        self._attr_native_step = 0.5
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float | None:
        targetTemp = self.data.domains["climatisation"]["climatisationSettings"].targetTemperature_C.value
        return float(targetTemp)

    async def async_set_native_value(self, value: float) -> None:
        if value > 10:
            await self.hass.async_add_executor_job(set_climatisation, self.data.vin.value, self._we_connect, "none", value)
