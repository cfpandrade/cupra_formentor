"""Sensor integration for Cupra We Connect."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from weconnect_cupra import weconnect_cupra

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPower,
    UnitOfTime,
    UnitOfTemperature,
    UnitOfSpeed,
)
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import CupraWeConnectEntity, get_object_value
from .const import DOMAIN

@dataclass
class CupraEntityDescription(SensorEntityDescription):
    """Describes Cupra We Connect sensor entity."""
    value: Callable = lambda x, y: x

SENSORS: tuple[CupraEntityDescription, ...] = (
    CupraEntityDescription(
        key="chargingState",
        name="Charging State",
        icon="mdi:ev-station",
        value=lambda data: data["charging"]["chargingStatus"].chargingState.value,
    ),
    CupraEntityDescription(
        key="remainingChargingTime",
        name="Remaining Charging Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data["charging"]["chargingStatus"].remainingChargingTimeToComplete_min.value,
    ),
    CupraEntityDescription(
        key="chargePower_kW",
        name="Charge Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data["charging"]["chargingStatus"].chargePower_kW.value,
    ),
    CupraEntityDescription(
        key="currentSOC_pct",
        name="State of Charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data["charging"]["batteryStatus"].currentSOC_pct.value,
    ),
    CupraEntityDescription(
        key="odometer_km",
        name="Odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data["measurements"]["odometerStatus"].odometer.value,
    ),
)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors for Cupra We Connect."""
    we_connect: weconnect_cupra.WeConnect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    await coordinator.async_config_entry_first_refresh()

    entities = [CupraSensor(sensor, we_connect, coordinator, index)
                for index, vehicle in enumerate(coordinator.data)
                for sensor in SENSORS]
    if entities:
        async_add_entities(entities)

class CupraSensor(CupraWeConnectEntity, SensorEntity):
    """Representation of a Cupra We Connect sensor."""
    entity_description: CupraEntityDescription

    def __init__(
        self,
        sensor: CupraEntityDescription,
        we_connect: weconnect_cupra.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize Cupra We Connect sensor."""
        super().__init__(we_connect, coordinator, index)
        self.entity_description = sensor
        self._attr_name = f"{self.data.nickname} {sensor.name}"
        self._attr_unique_id = f"{self.data.vin}-{sensor.key}"
        self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
        self._attr_state_class = sensor.state_class

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        return cast(StateType, get_object_value(self.entity_description.value(self.data.domains)))
