"""Sensor platform for Cupra Formentor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfLength,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CupraFormentorBaseEntity, get_object_value
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    entities = []

    # Add sensors for each vehicle
    for index, vehicle in enumerate(coordinator.data):
        vin = vehicle.vin.value

        # INFORMACIÓN DEL VEHÍCULO
        entities.extend([
            CupraVehicleInfoSensor(we_connect, coordinator, index, "vin", "VIN"),
            CupraVehicleInfoSensor(we_connect, coordinator, index, "nickname", "Nombre"),
            CupraVehicleInfoSensor(we_connect, coordinator, index, "model", "Modelo"),
            CupraVehicleInfoSensor(we_connect, coordinator, index, "brand", "Marca"),
        ])

        # ESTADO ACTUAL DE CARGA
        if hasattr(vehicle.domains, 'charging'):
            charging_domain = vehicle.domains.charging
            
            # Battery status
            if hasattr(charging_domain, 'batteryStatus'):
                entities.extend([
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "currentSOC_pct", "Estado de Carga",
                        PERCENTAGE, SensorDeviceClass.BATTERY
                    ),
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "cruisingRangeElectric_km", "Autonomía Eléctrica",
                        UnitOfLength.KILOMETERS, None
                    ),
                ])
            
            # Charging status
            if hasattr(charging_domain, 'chargingStatus'):
                entities.extend([
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "chargingState", "Estado de Carga",
                        None, None
                    ),
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "chargeMode", "Modo de Carga",
                        None, None
                    ),
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "chargeType", "Tipo de Carga",
                        None, None
                    ),
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "chargePower_kW", "Potencia de Carga",
                        "kW", SensorDeviceClass.POWER
                    ),
                ])
            
            # Plug status
            if hasattr(charging_domain, 'plugStatus'):
                entities.extend([
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "plugConnectionState", "Estado del Enchufe",
                        None, None
                    ),
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "plugLockState", "Bloqueo del Enchufe",
                        None, None
                    ),
                    CupraChargingSensor(
                        we_connect, coordinator, index,
                        "externalPower", "Energía Externa",
                        None, None
                    ),
                ])

        # CONFIGURACIÓN DE CARGA
        if hasattr(vehicle.domains, 'charging') and hasattr(vehicle.domains.charging, 'chargingSettings'):
            entities.extend([
                CupraChargingSettingSensor(
                    we_connect, coordinator, index,
                    "maxChargeCurrentAC", "Corriente Máxima AC",
                    UnitOfElectricCurrent.AMPERE, None
                ),
                CupraChargingSettingSensor(
                    we_connect, coordinator, index,
                    "targetSOC_pct", "SOC Objetivo",
                    PERCENTAGE, None
                ),
            ])

        # CLIMATIZACIÓN
        if hasattr(vehicle.domains, 'climatisation'):
            climatisation_domain = vehicle.domains.climatisation
            
            # Climate status
            if hasattr(climatisation_domain, 'climatisationStatus'):
                entities.append(
                    CupraClimateSensor(
                        we_connect, coordinator, index,
                        "climatisationState", "Estado Climatización",
                        None, None
                    )
                )
            
            # Climate settings
            if hasattr(climatisation_domain, 'climatisationSettings'):
                entities.append(
                    CupraClimateSensor(
                        we_connect, coordinator, index,
                        "targetTemperature_C", "Temperatura Objetivo",
                        UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE
                    )
                )

        # CONNECTION STATUS
        entities.append(
            CupraConnectionSensor(we_connect, coordinator, index)
        )

    async_add_entities(entities)


class CupraVehicleInfoSensor(CupraFormentorBaseEntity, SensorEntity):
    """Vehicle information sensors."""

    def __init__(
        self,
        we_connect,
        coordinator,
        index,
        attribute: str,
        name: str,
    ) -> None:
        """Initialize vehicle info sensor."""
        super().__init__(we_connect, coordinator, index)
        self._attribute = attribute
        self._attr_name = f"{self.data.nickname} {name}"
        self._attr_unique_id = f"{self.data.vin}_{attribute}"

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        if self._attribute == "vin":
            return self.data.vin.value
        elif self._attribute == "nickname":
            return self.data.nickname.value
        elif self._attribute == "model":
            return getattr(self.data.model, 'value', 'Unknown')
        elif self._attribute == "brand":
            # Try to get brand from specifications
            if hasattr(self.data, 'specifications') and hasattr(self.data.specifications, 'salesType'):
                return "CUPRA"
            return "CUPRA"
        return None


class CupraChargingSensor(CupraFormentorBaseEntity, SensorEntity):
    """Charging related sensors."""

    def __init__(
        self,
        we_connect,
        coordinator,
        index,
        attribute: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
    ) -> None:
        """Initialize charging sensor."""
        super().__init__(we_connect, coordinator, index)
        self._attribute = attribute
        self._attr_name = f"{self.data.nickname} {name}"
        self._attr_unique_id = f"{self.data.vin}_charging_{attribute}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        
        if unit and device_class in [SensorDeviceClass.BATTERY, SensorDeviceClass.POWER]:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        try:
            charging = self.data.domains.charging
            
            # Battery status attributes
            if hasattr(charging, 'batteryStatus'):
                battery = charging.batteryStatus
                if self._attribute == "currentSOC_pct":
                    return get_object_value(battery.currentSOC_pct)
                elif self._attribute == "cruisingRangeElectric_km":
                    return get_object_value(battery.cruisingRangeElectric_km)
            
            # Charging status attributes
            if hasattr(charging, 'chargingStatus'):
                status = charging.chargingStatus
                if self._attribute == "chargingState":
                    return get_object_value(status.chargingState)
                elif self._attribute == "chargeMode":
                    return get_object_value(status.chargeMode)
                elif self._attribute == "chargeType":
                    return get_object_value(status.chargeType)
                elif self._attribute == "chargePower_kW":
                    return get_object_value(status.chargePower_kW)
            
            # Plug status attributes
            if hasattr(charging, 'plugStatus'):
                plug = charging.plugStatus
                if self._attribute == "plugConnectionState":
                    return get_object_value(plug.plugConnectionState)
                elif self._attribute == "plugLockState":
                    return get_object_value(plug.plugLockState)
                elif self._attribute == "externalPower":
                    return get_object_value(plug.externalPower)
                    
        except Exception as e:
            _LOGGER.debug("Error getting charging attribute %s: %s", self._attribute, e)
            
        return None


class CupraChargingSettingSensor(CupraFormentorBaseEntity, SensorEntity):
    """Charging settings sensors."""

    def __init__(
        self,
        we_connect,
        coordinator,
        index,
        attribute: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
    ) -> None:
        """Initialize charging setting sensor."""
        super().__init__(we_connect, coordinator, index)
        self._attribute = attribute
        self._attr_name = f"{self.data.nickname} {name}"
        self._attr_unique_id = f"{self.data.vin}_charging_setting_{attribute}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        try:
            settings = self.data.domains.charging.chargingSettings
            
            if self._attribute == "maxChargeCurrentAC":
                value = get_object_value(settings.maxChargeCurrentAC)
                # Convert to numeric if possible
                if value == "maximum":
                    return "Máximo"
                elif value == "reduced":
                    return "Reducido"
                return value
            elif self._attribute == "targetSOC_pct":
                return get_object_value(settings.targetSOC_pct)
                
        except Exception as e:
            _LOGGER.debug("Error getting charging setting %s: %s", self._attribute, e)
            
        return None


class CupraClimateSensor(CupraFormentorBaseEntity, SensorEntity):
    """Climate related sensors."""

    def __init__(
        self,
        we_connect,
        coordinator,
        index,
        attribute: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
    ) -> None:
        """Initialize climate sensor."""
        super().__init__(we_connect, coordinator, index)
        self._attribute = attribute
        self._attr_name = f"{self.data.nickname} {name}"
        self._attr_unique_id = f"{self.data.vin}_climate_{attribute}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        
        if device_class == SensorDeviceClass.TEMPERATURE:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        try:
            climatisation = self.data.domains.climatisation
            
            if self._attribute == "climatisationState" and hasattr(climatisation, 'climatisationStatus'):
                state = get_object_value(climatisation.climatisationStatus.climatisationState)
                return "Encendido" if state == "on" else "Apagado"
            elif self._attribute == "targetTemperature_C" and hasattr(climatisation, 'climatisationSettings'):
                return get_object_value(climatisation.climatisationSettings.targetTemperature_C)
                
        except Exception as e:
            _LOGGER.debug("Error getting climate attribute %s: %s", self._attribute, e)
            
        return None


class CupraConnectionSensor(CupraFormentorBaseEntity, SensorEntity):
    """Connection status sensor."""

    def __init__(self, we_connect, coordinator, index) -> None:
        """Initialize connection sensor."""
        super().__init__(we_connect, coordinator, index)
        self._attr_name = f"{self.data.nickname} Conexión"
        self._attr_unique_id = f"{self.data.vin}_connection"

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        try:
            # Check if vehicle has connection status
            if hasattr(self.data, 'status') and hasattr(self.data.status, 'connectionState'):
                state = get_object_value(self.data.status.connectionState)
                return "En línea" if state == "online" else "Fuera de línea"
            # Alternative: check domains
            elif hasattr(self.data, 'domains'):
                return "En línea"
        except Exception as e:
            _LOGGER.debug("Error getting connection status: %s", e)
            
        return "Desconocido"