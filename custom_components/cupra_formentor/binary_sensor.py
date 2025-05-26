"""Binary sensor platform for Cupra Formentor integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up binary sensors for Cupra Formentor."""
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    entities = []

    # Add binary sensors for each vehicle
    for index, vehicle in enumerate(coordinator.data):
        # Only add binary sensors that we know exist
        if hasattr(vehicle.domains, 'charging'):
            entities.extend([
                CupraChargingConnectedSensor(we_connect, coordinator, index),
                CupraExternalPowerSensor(we_connect, coordinator, index),
            ])

    if entities:
        async_add_entities(entities)

class CupraChargingConnectedSensor(CupraFormentorBaseEntity, BinarySensorEntity):
    """Binary sensor for charging cable connected."""

    def __init__(self, we_connect, coordinator, index) -> None:
        """Initialize binary sensor."""
        super().__init__(we_connect, coordinator, index)
        self._attr_name = f"{self.data.nickname} Cable Conectado"
        self._attr_unique_id = f"{self.data.vin}_charging_cable_connected"

    @property
    def is_on(self) -> bool | None:
        """Return true if charging cable is connected."""
        try:
            if hasattr(self.data.domains.charging, 'plugStatus'):
                state = get_object_value(self.data.domains.charging.plugStatus.plugConnectionState)
                return state == "connected"
        except Exception as e:
            _LOGGER.debug("Error getting plug connection state: %s", e)
        return None


class CupraExternalPowerSensor(CupraFormentorBaseEntity, BinarySensorEntity):
    """Binary sensor for external power available."""

    def __init__(self, we_connect, coordinator, index) -> None:
        """Initialize binary sensor."""
        super().__init__(we_connect, coordinator, index)
        self._attr_name = f"{self.data.nickname} Energía Externa"
        self._attr_unique_id = f"{self.data.vin}_external_power"

    @property
    def is_on(self) -> bool | None:
        """Return true if external power is available."""
        try:
            if hasattr(self.data.domains.charging, 'plugStatus'):
                state = get_object_value(self.data.domains.charging.plugStatus.externalPower)
                return state == "available"
        except Exception as e:
            _LOGGER.debug("Error getting external power state: %s", e)
        return None