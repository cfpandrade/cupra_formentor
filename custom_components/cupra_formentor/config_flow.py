"""Config flow for Cupra Formentor integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Schema para el formulario
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("service", default="MyCupra"): vol.In(["MyCupra"]),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    # Import with correct structure
    try:
        from weconnect.weconnect import WeConnect
        from weconnect.errors import AuthentificationError, APIError
    except ImportError as err:
        _LOGGER.error("Failed to import weconnect: %s", err)
        raise CannotConnect from err

    _LOGGER.debug("Validating credentials for user: %s", data["username"])

    try:
        we_connect = WeConnect(
            username=data["username"],
            password=data["password"],
            updateAfterLogin=False,
            loginOnInit=False,
            timeout=10
        )

        # Test login
        await hass.async_add_executor_job(we_connect.login)
        _LOGGER.debug("Login successful")

        # Test update to get vehicles
        await hass.async_add_executor_job(we_connect.update)
        _LOGGER.debug("Update successful")

        if not we_connect.vehicles:
            _LOGGER.error("No vehicles found in account")
            raise NoVehiclesFound

        # Log found vehicles
        for vin, vehicle in we_connect.vehicles.items():
            model = getattr(getattr(vehicle, 'model', None), 'value', 'Unknown')
            _LOGGER.info("Found vehicle: VIN=%s, Model=%s", vin, model)

    except AuthentificationError as ex:
        _LOGGER.error("Authentication failed: %s", ex)
        raise InvalidAuth from ex
    except APIError as ex:
        _LOGGER.error("API error: %s", ex)
        raise CannotConnect from ex
    except Exception as ex:
        _LOGGER.error("Unexpected error: %s", ex)
        raise CannotConnect from ex

    return {"title": "Cupra Formentor"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cupra Formentor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(user_input["username"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except NoVehiclesFound:
                errors["base"] = "no_vehicles_found"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class NoVehiclesFound(HomeAssistantError):
    """Error to indicate no vehicles were found."""