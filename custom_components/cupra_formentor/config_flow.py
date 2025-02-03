"""Config flow for Cupra We Connect integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.service import Service
from weconnect_cupra.errors import AuthentificationError, APIError

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import selector

from . import patch  # Applies the monkey patch
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Schema para el formulario
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("service", default="MyCupra"): selector(
            {
                "select": {
                    "options": ["MyCupra"]
                }
            }
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Valida las credenciales y conexión con la API."""
    _LOGGER.debug(f'Validando credenciales: usuario={data["username"]}, servicio={data["service"]}')

    try:
        we_connect = weconnect_cupra.WeConnect(
            username=data["username"],
            password=data["password"],
            service=Service(data["service"]),
            updateAfterLogin=False,
            loginOnInit=False,
        )

        try:
            # Paso 1: Login
            _LOGGER.debug("Iniciando sesión...")
            await hass.async_add_executor_job(we_connect.login)
            _LOGGER.debug("Login exitoso")

            # Paso 2: Obtener datos del vehículo
            _LOGGER.debug("Actualizando datos del vehículo...")
            await hass.async_add_executor_job(we_connect.update)
            _LOGGER.debug("Actualización completada")

            if we_connect.vehicles:
                for vin, vehicle in we_connect.vehicles.items():
                    _LOGGER.debug(f"VIN encontrado: {vin}")
                    try:
                        # Obtener todos los datos del vehículo en formato dict
                        vehicle_data = vehicle.to_dict()

                        # Registrar todos los datos en los logs
                        _LOGGER.debug(f"Datos completos del vehículo ({vin}): {vehicle_data}")

                        # Filtrar datos con valores no válidos
                        filtered_data = {
                            key: value for key, value in vehicle_data.items()
                            if value not in [None, "Unknown", "unknown"]
                        }

                        # Registrar los datos filtrados
                        _LOGGER.debug(f"Datos filtrados del vehículo ({vin}): {filtered_data}")

                        # Advertencia si no hay datos válidos
                        if not filtered_data:
                            _LOGGER.warning(f"Todos los sensores para el vehículo {vin} están vacíos o no válidos.")

                    except Exception as e:
                        _LOGGER.error(f"Error al leer datos del vehículo: {e}")
            else:
                _LOGGER.error("No se encontraron vehículos en la cuenta")
                raise NoVehiclesFound

        except AuthentificationError as ex:
            _LOGGER.error(f"Error de autenticación: {ex}", exc_info=True)
            raise InvalidAuth from ex
        except APIError as ex:
            _LOGGER.error(f"Error de la API: {ex}", exc_info=True)
            raise CannotConnect from ex
        except KeyError as ex:
            _LOGGER.error(f"Campo faltante en la respuesta: {ex}", exc_info=True)
            raise CannotConnect from ex
        except Exception as ex:
            _LOGGER.error(f"Error inesperado: {ex}", exc_info=True)
            raise CannotConnect from ex

    except Exception as setup_ex:
        _LOGGER.error(f"Error en el flujo de configuración: {setup_ex}", exc_info=True)
        raise

    return {"title": "Cupra We Connect"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Maneja el flujo de configuración."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Maneja el paso inicial de configuración."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except NoVehiclesFound:
            errors["base"] = "no_vehicles_found"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error inesperado")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


# Clases de excepciones
class CannotConnect(HomeAssistantError):
    """Error de conexión con la API."""

class InvalidAuth(HomeAssistantError):
    """Error de autenticación."""

class NoVehiclesFound(HomeAssistantError):
    """No se encontraron vehículos."""