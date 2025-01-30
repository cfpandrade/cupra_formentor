"""Binary sensor integration for Cupra Formentor."""
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
