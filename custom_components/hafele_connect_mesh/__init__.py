"""Häfele Connect Mesh integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import aiohttp

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Häfele Connect Mesh from a config entry."""
    # Check if this is a migrated entry
    if "api_token" not in entry.data and "api_token" in entry.data.get("old_config", {}):
        new_data = dict(entry.data)
        new_data["api_token"] = entry.data["old_config"]["api_token"]
        hass.config_entries.async_update_entry(entry, data=new_data)
        _LOGGER.info("Migrated API token from old configuration")

    session = async_get_clientsession(hass)
    api_client = ConnectMeshAPI(session, entry.data["api_token"])
    
    async def async_update_data():
        """Fetch data from API."""
        devices = entry.data["devices"]
        return {device["uniqueId"]: await api_client.get_device_status(device["uniqueId"]) for device in devices}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="hafele_connect_mesh",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api_client": api_client,
        "coordinator": coordinator,
        "devices": entry.data["devices"]
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async def get_device_status(call: ServiceCall) -> None:
        """Handle the service call."""
        device_id = call.data["device_id"]
        status = await api_client.get_device_status(device_id)
        hass.states.async_set(f"{DOMAIN}.{device_id}_status", "retrieved", status)

    hass.services.async_register(DOMAIN, "get_device_status", get_device_status)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

class ConnectMeshAPI:
    """API client for Connect Mesh."""

    def __init__(self, session: aiohttp.ClientSession, api_token: str):
        """Initialize the API client."""
        self.session = session
        self.api_token = api_token
        self.base_url = "https://cloud.connect-mesh.io/api/core"

    async def get_device_status(self, unique_id: str):
        """Get the status of a device."""
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {self.api_token}"
        }
        async with self.session.get(f"{self.base_url}/devices/{unique_id}/status", headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                _LOGGER.error(f"Failed to get device status. Status code: {response.status}")
                return None

    async def set_power(self, unique_id: str, power: bool):
        """Set the power state of a device."""
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        data = {
            "power": "on" if power else "off",
            "uniqueId": unique_id,
            "acknowledged": True,
            "retries": 0,
            "timeout_ms": 10000
        }
        async with self.session.put(f"{self.base_url}/devices/power", headers=headers, json=data) as response:
            if response.status != 200:
                _LOGGER.error(f"Failed to set power state. Status code: {response.status}")

    async def set_lightness(self, unique_id: str, lightness: float):
        """Set the lightness of a device."""
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        data = {
            "lightness": lightness,
            "uniqueId": unique_id,
            "acknowledged": True,
            "retries": 0,
            "timeout_ms": 10000
        }
        async with self.session.put(f"{self.base_url}/devices/lightness", headers=headers, json=data) as response:
            if response.status != 200:
                _LOGGER.error(f"Failed to set lightness. Status code: {response.status}")
            else:
                _LOGGER.debug(f"Set lightness to {lightness} for device {unique_id}")

    async def set_temperature(self, unique_id: str, temperature: int):
        """Set the color temperature of a device."""
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        data = {
            "temperature": temperature,
            "uniqueId": unique_id,
            "acknowledged": True,
            "retries": 0,
            "timeout_ms": 10000
        }
        async with self.session.put(f"{self.base_url}/devices/temperature", headers=headers, json=data) as response:
            if response.status != 200:
                _LOGGER.error(f"Failed to set temperature. Status code: {response.status}")
            else:
                _LOGGER.debug(f"Set temperature to {temperature}K for device {unique_id}")


    async def set_hue_saturation(self, unique_id: str, hue: float, saturation: float):
        """Set the hue and saturation of a device."""
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        data = {
            "hue": min(360, max(0, hue)),  # Ensure hue is between 0 and 360
            "saturation": min(1, max(0, saturation)),  # Ensure saturation is between 0 and 1
            "uniqueId": unique_id,
            "acknowledged": True,
            "retries": 0,
            "timeout_ms": 10000
        }
        async with self.session.put(f"{self.base_url}/devices/hue_saturation", headers=headers, json=data) as response:
            if response.status != 200:
                _LOGGER.error(f"Failed to set hue and saturation. Status code: {response.status}")
            else:
                _LOGGER.debug(f"Set hue to {hue} and saturation to {saturation} for device {unique_id}")
