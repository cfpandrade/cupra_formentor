"""The Cupra Formentor integration."""
from __future__ import annotations

from datetime import timedelta
import logging
import asyncio
import time

from weconnect import weconnect
from weconnect.service import Service
from weconnect.elements.control_operation import ControlOperation

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR, Platform.NUMBER, Platform.DEVICE_TRACKER]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cupra Formentor from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    _we_connect = weconnect.WeConnect(
        username=entry.data["username"],
        password=entry.data["password"],
        service=Service(entry.data["service"]),
        updateAfterLogin=False,
        loginOnInit=False,
        timeout=10
    )
    
    await hass.async_add_executor_job(_we_connect.login)
    await hass.async_add_executor_job(_we_connect.update)

    async def async_update_data():
        """Fetch data from Cupra API."""

        try:
            await asyncio.wait_for(
                hass.async_add_executor_job(_we_connect.update),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout updating weconnect")
            return hass.data[DOMAIN][entry.entry_id + "_vehicles"]
        except Exception:
            _LOGGER.error("Unknown error while updating weconnect", exc_info=1)
            return hass.data[DOMAIN][entry.entry_id + "_vehicles"]

        vehicles = []

        for vin, vehicle in _we_connect.vehicles.items():
            vehicles.append(vehicle)

        hass.data[DOMAIN][entry.entry_id + "_vehicles"] = vehicles
        return vehicles

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=300),
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id + "_coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id] = _we_connect
    hass.data[DOMAIN][entry.entry_id + "_vehicles"] = []

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Setup components
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    async def cupra_formentor_start_stop_charging(call: ServiceCall) -> None:

        vin = call.data["vin"]
        start_stop = call.data["start_stop"]

        if (
            await hass.async_add_executor_job(
                start_stop_charging,
                vin,
                _we_connect,
                start_stop,
            )
            is False
        ):
            _LOGGER.error("Cannot send charging request to car")

    @callback
    async def cupra_formentor_set_climatisation(call: ServiceCall) -> None:

        vin = call.data["vin"]
        start_stop = call.data["start_stop"]
        target_temperature = 0
        if "target_temp" in call.data:
            target_temperature = call.data["target_temp"]

        if (
            await hass.async_add_executor_job(
                set_climatisation,
                vin,
                _we_connect,
                start_stop,
                target_temperature,
            )
            is False
        ):
            _LOGGER.error("Cannot send climate request to car")

    @callback
    async def cupra_formentor_set_target_soc(call: ServiceCall) -> None:

        vin = call.data["vin"]
        target_soc = 0
        if "target_soc" in call.data:
            target_soc = call.data["target_soc"]

        if (
            await hass.async_add_executor_job(
                set_target_soc,
                vin,
                _we_connect,
                target_soc,
            )
            is False
        ):
            _LOGGER.error("Cannot send target soc request to car")

    @callback
    async def cupra_formentor_set_ac_charge_speed(call: ServiceCall) -> None:

        vin = call.data["vin"]
        if "maximum_reduced" in call.data:
            if (
                await hass.async_add_executor_job(
                    set_ac_charging_speed,
                    vin,
                    _we_connect,
                    call.data["maximum_reduced"],
                )
                is False
            ):
                _LOGGER.error("Cannot send ac speed request to car")

    # Register our services with Home Assistant.
    hass.services.async_register(
        DOMAIN, "cupra_formentor_start_stop_charging", cupra_formentor_start_stop_charging
    )

    hass.services.async_register(
        DOMAIN, "cupra_formentor_set_climatisation", cupra_formentor_set_climatisation
    )
    hass.services.async_register(
        DOMAIN, "cupra_formentor_set_target_soc", cupra_formentor_set_target_soc
    )
    hass.services.async_register(
        DOMAIN, "cupra_formentor_set_ac_charge_speed", cupra_formentor_set_ac_charge_speed
    )

    return True


def start_stop_charging(
    call_data_vin, api: weconnect.WeConnect, operation: str
) -> bool:
    """Start of stop charging of your Cupra Formentor."""

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:

            if operation == "start":
                try:
                    if (
                        vehicle.controls.chargingControl is not None
                        and vehicle.controls.chargingControl.enabled
                    ):
                        vehicle.controls.chargingControl.value = ControlOperation.START
                        _LOGGER.info("Sent start charging call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False

            if operation == "stop":
                try:
                    if (
                        vehicle.controls.chargingControl is not None
                        and vehicle.controls.chargingControl.enabled
                    ):
                        vehicle.controls.chargingControl.value = ControlOperation.STOP
                        _LOGGER.info("Sent stop charging call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False
    return True


def set_ac_charging_speed(
    call_data_vin, api: weconnect.WeConnect, charging_speed
) -> bool:
    """Set charging speed in your Cupra Formentor."""

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:
            try:
                # Handle None values for hybrid vehicles
                charging_settings = vehicle.domains.get("charging", {}).get("chargingSettings")
                if charging_settings and hasattr(charging_settings, 'maxChargeCurrentAC'):
                    current_speed = getattr(charging_settings.maxChargeCurrentAC, 'value', None)
                    if current_speed is not None and charging_speed != current_speed:
                        charging_settings.maxChargeCurrentAC.value = charging_speed
                        _LOGGER.info("Sent charging speed call to the car")
                else:
                    _LOGGER.warning("Charging settings not available for this vehicle")
            except Exception as exc:
                _LOGGER.error("Failed to send request to car - %s", exc)
                return False

    return True


def set_target_soc(call_data_vin, api: weconnect.WeConnect, target_soc: int) -> bool:
    """Set target SOC in your Cupra Formentor."""

    target_soc = int(target_soc)

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:
            try:
                # Handle None values for hybrid vehicles
                charging_settings = vehicle.domains.get("charging", {}).get("chargingSettings")
                if charging_settings and hasattr(charging_settings, 'targetSOC_pct'):
                    current_soc = getattr(charging_settings.targetSOC_pct, 'value', None)
                    if target_soc > 10 and current_soc is not None and target_soc != current_soc:
                        charging_settings.targetSOC_pct.value = target_soc
                        _LOGGER.info("Sent target SoC call to the car")
                else:
                    _LOGGER.warning("Target SOC setting not available for this vehicle")
            except Exception as exc:
                _LOGGER.error("Failed to send request to car - %s", exc)
                return False
    return True


def set_climatisation(
    call_data_vin, api: weconnect.WeConnect, operation: str, target_temperature: float
) -> bool:
    """Set climate in your Cupra Formentor."""

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:

            try:
                # Handle temperature setting
                climatisation_settings = vehicle.domains.get("climatisation", {}).get("climatisationSettings")
                if (
                    target_temperature > 10
                    and climatisation_settings 
                    and hasattr(climatisation_settings, 'targetTemperature_C')
                ):
                    current_temp = getattr(climatisation_settings.targetTemperature_C, 'value', None)
                    if current_temp is not None and target_temperature != current_temp:
                        climatisation_settings.targetTemperature_C.value = float(target_temperature)
                        _LOGGER.info("Sent target temperature call to the car")
            except Exception as exc:
                _LOGGER.error("Failed to send temperature request to car - %s", exc)
                return False

            if operation == "start":
                try:
                    if (
                        vehicle.controls.climatizationControl is not None
                        and vehicle.controls.climatizationControl.enabled
                    ):
                        vehicle.controls.climatizationControl.value = ControlOperation.START
                        _LOGGER.info("Sent start climate call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send climate start request to car - %s", exc)
                    return False

            if operation == "stop":
                try:
                    if (
                        vehicle.controls.climatizationControl is not None
                        and vehicle.controls.climatizationControl.enabled
                    ):
                        vehicle.controls.climatizationControl.value = ControlOperation.STOP
                        _LOGGER.info("Sent stop climate call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send climate stop request to car - %s", exc)
                    return False
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def get_object_value(value) -> str:
    """Get value from object or enum."""

    while hasattr(value, "value"):
        value = value.value

    return value


class CupraFormentorBaseEntity(CoordinatorEntity):
    """Common base for Cupra Formentor entities."""

    _attr_attribution = "Data provided by Cupra Connect"

    def __init__(
        self,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.we_connect = we_connect
        self.index = index

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"cupra{self.data.vin}")},
            manufacturer="Cupra",
            model=f"{self.data.model}",
            name=f"{self.data.nickname} ({self.data.vin})",
        )

    @property
    def data(self):
        """Shortcut to access coordinator data for the entity."""
        return self.coordinator.data[self.index]