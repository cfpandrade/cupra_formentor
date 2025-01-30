"""Config flow for Cupra Formentor integration."""
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
    """Validates credentials and API connection."""
    _LOGGER.debug(f'Validating credentials: user={data["username"]}, service={data["service"]}')
    
    try:
        we_connect = weconnect_cupra.WeConnect(
            username=data["username"],
            password=data["password"],
            service=Service(data["service"]),
            updateAfterLogin=False,
            loginOnInit=False,
        )

        _LOGGER.debug("Logging in...")
        await hass.async_add_executor_job(we_connect.login)
        _LOGGER.debug("Login successful")

        _LOGGER.debug("Updating vehicle data...")
        await hass.async_add_executor_job(we_connect.update)
        _LOGGER.debug("Update completed")

        if not we_connect.vehicles:
            _LOGGER.error("No vehicles found in the account")
            raise NoVehiclesFound

        for vin, vehicle in we_connect.vehicles.items():
            _LOGGER.debug(f"Found VIN: {vin}")
            vehicle_data = {attr: getattr(vehicle, attr, None) for attr in dir(vehicle) if not attr.startswith("_")}
            _LOGGER.debug(f"Extracted vehicle data ({vin}): {vehicle_data}")
            
            if not vehicle_data:
                _LOGGER.warning(f"No valid data extracted for vehicle {vin}.")
    
    except AuthentificationError as ex:
        _LOGGER.error("Authentication error", exc_info=True)
        raise InvalidAuth from ex
    except APIError as ex:
        _LOGGER.error("API error", exc_info=True)
        raise CannotConnect from ex
    except Exception as ex:
        _LOGGER.error("Unexpected error", exc_info=True)
        raise CannotConnect from ex
    
    return {"title": "Cupra Formentor"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles the configuration flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handles the initial step of configuration."""
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
        except Exception:
            _LOGGER.exception("Unexpected error")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error connecting to the API."""

class InvalidAuth(HomeAssistantError):
    """Authentication error."""

class NoVehiclesFound(HomeAssistantError):
    """No vehicles found."""