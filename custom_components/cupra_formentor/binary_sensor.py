"""Binary sensor integration for Cupra We Connect."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.elements.plug_status import PlugStatus
from weconnect_cupra.elements.window_heating_status import WindowHeatingStatus
from weconnect_cupra.elements.access_control_state import AccessControlState
from weconnect_cupra.elements.connection_state import ConnectionState
from weconnect_cupra.elements.lights_status import LightsStatus
from weconnect_cupra.elements.engine_status import EngineStatus
from weconnect_cupra.elements.door_status import DoorStatus
from weconnect_cupra.elements.battery_status import BatteryStatus
from weconnect_cupra.elements.parking_brake_status import ParkingBrakeStatus
from weconnect_cupra.elements.air_conditioning_status import AirConditioningStatus

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import CupraWeConnectEntity, get_object_value
from .const import DOMAIN

@dataclass
class CupraBinaryEntityDescription(BinarySensorEntityDescription):
    """Describes a Cupra We Connect binary sensor entity."""
    value: Callable = lambda x, y: x
    on_value: object | None = None

SENSORS: tuple[CupraBinaryEntityDescription, ...] = (
    CupraBinaryEntityDescription(
        key="plugConnectionState",
        name="Plug Connection State",
        device_class=BinarySensorDeviceClass.PLUG,
        value=lambda data: data["charging"]["plugStatus"].plugConnectionState.value,
        on_value=PlugStatus.PlugConnectionState.CONNECTED,
    ),
    CupraBinaryEntityDescription(
        key="plugLockState",
        name="Plug Lock State",
        device_class=BinarySensorDeviceClass.LOCK,
        value=lambda data: data["charging"]["plugStatus"].plugLockState.value,
        on_value=PlugStatus.PlugLockState.LOCKED,
    ),
    CupraBinaryEntityDescription(
        key="doorLockStatus",
        name="Door Lock Status",
        device_class=BinarySensorDeviceClass.LOCK,
        value=lambda data: data["access"]["accessStatus"].doorLockStatus.value,
        on_value=AccessControlState.LockState.UNLOCKED,
    ),
    CupraBinaryEntityDescription(
        key="isOnline",
        name="Car Is Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value=lambda data: data["status"]["connectionStatus"].connectionState.value,
        on_value=ConnectionState.ConnectionState.ONLINE,
    ),
    CupraBinaryEntityDescription(
        key="windowHeatingEnabled",
        name="Window Heating Enabled",
        device_class=BinarySensorDeviceClass.HEAT,
        value=lambda data: data["climatisation"]["windowHeatingStatus"].windows["front"].windowHeatingState.value,
        on_value=WindowHeatingStatus.Window.WindowHeatingState.ON,
    ),
    CupraBinaryEntityDescription(
        key="engineStatus",
        name="Engine Status",
        device_class=BinarySensorDeviceClass.POWER,
        value=lambda data: data["access"]["accessStatus"].engineStatus.value,
        on_value=EngineStatus.EngineState.ON,
    ),
    CupraBinaryEntityDescription(
        key="lightsStatus",
        name="Lights Status",
        device_class=BinarySensorDeviceClass.LIGHT,
        value=lambda data: data["access"]["accessStatus"].lightsStatus.value,
        on_value=LightsStatus.LightsState.ON,
    ),
    CupraBinaryEntityDescription(
        key="doorOpenStatus",
        name="Door Open Status",
        device_class=BinarySensorDeviceClass.DOOR,
        value=lambda data: data["access"]["accessStatus"].doors["frontLeft"].openState.value,
        on_value=DoorStatus.DoorState.OPEN,
    ),
    CupraBinaryEntityDescription(
        key="parkingBrakeStatus",
        name="Parking Brake Engaged",
        device_class=BinarySensorDeviceClass.SAFETY,
        value=lambda data: data["status"]["parkingBrakeStatus"].value,
        on_value=ParkingBrakeStatus.Engaged,
    ),
    CupraBinaryEntityDescription(
        key="batteryCharging",
        name="Battery Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value=lambda data: data["charging"]["batteryStatus"].charging.value,
        on_value=BatteryStatus.ChargingState.CHARGING,
    ),
    CupraBinaryEntityDescription(
        key="airConditioningActive",
        name="Air Conditioning Active",
        device_class=BinarySensorDeviceClass.POWER,
        value=lambda data: data["climatisation"]["airConditioningStatus"].active.value,
        on_value=AirConditioningStatus.ActiveState.ON,
    ),
)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up binary sensors for Cupra We Connect."""
    we_connect: weconnect_cupra.WeConnect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    await coordinator.async_config_entry_first_refresh()

    entities = [CupraBinarySensor(sensor, we_connect, coordinator, index)
                for index, vehicle in enumerate(coordinator.data)
                for sensor in SENSORS]

    if entities:
        async_add_entities(entities)

class CupraBinarySensor(CupraWeConnectEntity, BinarySensorEntity):
    """Representation of a Cupra We Connect binary sensor."""

    entity_description: CupraBinaryEntityDescription

    def __init__(
        self,
        sensor: CupraBinaryEntityDescription,
        we_connect: weconnect_cupra.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize Cupra We Connect binary sensor."""
        super().__init__(we_connect, coordinator, index)
        self.entity_description = sensor
        self._attr_name = f"{self.data.nickname} {sensor.name}"
        self._attr_unique_id = f"{self.data.vin}-{sensor.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        try:
            state = self.entity_description.value(self.data.domains)
            if isinstance(state, bool):
                return state
            return get_object_value(state) == get_object_value(self.entity_description.on_value)
        except KeyError:
            return None