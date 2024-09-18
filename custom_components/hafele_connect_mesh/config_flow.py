"""Config flow for Häfele Connect Mesh integration."""
from __future__ import annotations

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("api_token"): str,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Häfele Connect Mesh."""

    VERSION = 2
    
    def __init__(self):
        """Initialize the config flow."""
        self.api_token = None
        self.networks = None
        self.selected_network_id = None
        self.devices = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        # Check for existing entries
        existing_entry = next((entry for entry in self._async_current_entries() if entry.domain == DOMAIN), None)
        if existing_entry:
            return await self.async_step_reauth(user_input)

        if user_input is not None:
            self.api_token = user_input["api_token"]
            return await self.async_step_select_network()

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors,
            description_placeholders={
                "setup_info": "For more information and setup guide, visit: https://github.com/guillaumeseur/hafele_connect_mesh\n\nPlease obtain your API key from: https://cloud.connect-mesh.io/developer"
            }
        )

    async def async_step_reauth(self, user_input=None) -> FlowResult:
        """Handle reauthorization."""
        if user_input is not None:
            existing_entry = next((entry for entry in self._async_current_entries() if entry.domain == DOMAIN), None)
            if existing_entry:
                self.hass.config_entries.async_update_entry(existing_entry, data=user_input)
                await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={
                "setup_info": "Please re-enter your API token to update your existing configuration."
            }
        )

    async def async_step_select_network(self, user_input=None) -> FlowResult:
        """Handle network selection."""
        errors = {}
        if user_input is not None:
            self.selected_network_id = user_input["network"]
            return await self.async_step_process_devices()

        if self.networks is None:
            self.networks = await self._fetch_networks()

        if not self.networks:
            return self.async_abort(reason="no_networks")

        network_schema = vol.Schema({
            vol.Required("network"): vol.In({net["id"]: net["name"] for net in self.networks})
        })

        return self.async_show_form(
            step_id="select_network",
            data_schema=network_schema,
            errors=errors,
            description_placeholders={
                "select_info": "Please select one network to add to Home Assistant."
            }
        )

    async def async_step_process_devices(self, user_input=None) -> FlowResult:
        """Process devices for the selected network."""
        if self.devices is None:
            self.devices = await self._fetch_devices()
            self.devices = [device for device in self.devices if device["networkId"] == self.selected_network_id]

        processed_devices = []
        for device in self.devices:
            status = await self._fetch_device_status(device["uniqueId"])
            device_type = self._determine_device_type(status)
            processed_devices.append({
                "uniqueId": device["uniqueId"],
                "name": device["name"],
                "type": device_type
            })

        # Create the config entry
        return self.async_create_entry(
            title="Häfele Connect Mesh",
            data={
                "api_token": self.api_token,
                "network_id": self.selected_network_id,
                "devices": processed_devices
            }
        )

    async def _fetch_networks(self):
        """Fetch networks from the API."""
        session = async_get_clientsession(self.hass)
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {self.api_token}"
        }
        try:
            async with session.get("https://cloud.connect-mesh.io/api/core/networks", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    _LOGGER.error(f"Failed to fetch networks. Status code: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching networks: {e}")
            return None

    async def _fetch_devices(self):
        """Fetch devices from the API."""
        session = async_get_clientsession(self.hass)
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        try:
            async with session.get("https://cloud.connect-mesh.io/api/core/devices", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    _LOGGER.error(f"Failed to fetch devices. Status code: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching devices: {e}")
            return None

    async def _fetch_device_status(self, unique_id):
        """Fetch status for a specific device."""
        session = async_get_clientsession(self.hass)
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {self.api_token}"
        }
        try:
            async with session.get(f"https://cloud.connect-mesh.io/api/core/devices/{unique_id}/status", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    _LOGGER.error(f"Failed to fetch device status for {unique_id}. Status code: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching device status for {unique_id}: {e}")
            return None

    def _determine_device_type(self, status):
        """Determine the device type based on its status."""
        if status is None:
            _LOGGER.warning("Device status is None, defaulting to 'switch' type")
            return "switch"
        
        abstraction = status.get("abstraction")
        if abstraction == "Multiwhite":
            return "temperature"
        elif abstraction == "RGB":
            return "rgb"
        elif abstraction == "Light":
            return "brightness"
        else:
            return "switch"
