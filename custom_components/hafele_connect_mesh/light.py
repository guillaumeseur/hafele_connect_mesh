"""Platform for light integration."""
from __future__ import annotations

import logging
from typing import Any
from datetime import timedelta
import asyncio

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util.color import (
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

MIN_KELVIN = 2700
MAX_KELVIN = 5000

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Connect Mesh light platform."""
    api_client = hass.data[DOMAIN][entry.entry_id]["api_client"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    
    async def async_update_data():
        """Fetch data from API."""
        return {device["uniqueId"]: await api_client.get_device_status(device["uniqueId"]) for device in devices}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="light",
        update_method=async_update_data,
        update_interval=timedelta(seconds=10),  # Reduced update interval
    )

    await coordinator.async_refresh()

    entities = []
    for device in devices:
        entities.append(ConnectMeshLight(coordinator, api_client, device))
    
    async_add_entities(entities)

class ConnectMeshLight(CoordinatorEntity, LightEntity):
    """Representation of a Connect Mesh Light."""

    def __init__(self, coordinator, api_client, device):
        """Initialize a Connect Mesh Light."""
        super().__init__(coordinator)
        self._api_client = api_client
        self._device = device
        self._attr_unique_id = device["uniqueId"]
        self._attr_name = device["name"]
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_min_mireds = color_temperature_kelvin_to_mired(MAX_KELVIN)
        self._attr_max_mireds = color_temperature_kelvin_to_mired(MIN_KELVIN)
        self._state = None
        self._brightness = None
        self._color_temp = None
        self._hs_color = None
        self._last_known_brightness = None
        self._pending_update = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self._pending_update:
            self._update_attributes()
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def color_temp(self) -> int | None:
        """Return the CT color value in mireds."""
        return self._color_temp

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the hs color value."""
        return self._hs_color

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        self._state = True
        self._pending_update = True

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            self._brightness = brightness
            self._last_known_brightness = brightness
            await self._api_client.set_lightness(self._attr_unique_id, self._ha_to_api_brightness(brightness))
        elif not self._brightness and self._last_known_brightness:
            self._brightness = self._last_known_brightness
            await self._api_client.set_lightness(self._attr_unique_id, self._ha_to_api_brightness(self._last_known_brightness))
        else:
            await self._api_client.set_power(self._attr_unique_id, True)

        if ATTR_COLOR_TEMP in kwargs:
            kelvin = color_temperature_mired_to_kelvin(kwargs[ATTR_COLOR_TEMP])
            kelvin = max(MIN_KELVIN, min(MAX_KELVIN, kelvin))
            self._color_temp = kwargs[ATTR_COLOR_TEMP]
            await self._api_client.set_temperature(self._attr_unique_id, kelvin)

        if ATTR_HS_COLOR in kwargs:
            self._hs_color = kwargs[ATTR_HS_COLOR]
            hue, saturation = self._hs_color
            hue_api = hue / 360 * 65535
            saturation_api = saturation / 100
            await self._api_client.set_hue_saturation(self._attr_unique_id, hue_api, saturation_api)

        self.async_write_ha_state()
        await self._async_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._state = False
        self._pending_update = True
        await self._api_client.set_power(self._attr_unique_id, False)
        self.async_write_ha_state()
        await self._async_update_ha_state()

    @staticmethod
    def _api_to_ha_brightness(value: int) -> int:
        """Convert API brightness (0-65535) to HA brightness (0-255)."""
        return round((value / 65535) * 255)

    @staticmethod
    def _ha_to_api_brightness(value: int) -> float:
        """Convert HA brightness (0-255) to API brightness (0-1)."""
        return value / 255

    def _update_attributes(self):
        """Update attributes based on the latest data from the coordinator."""
        state = self.coordinator.data.get(self._attr_unique_id, {}).get("state", {})
        self._state = state.get("power", False)
        
        if "lightness" in state:
            self._brightness = self._api_to_ha_brightness(state["lightness"])
            if self._state:
                self._last_known_brightness = self._brightness

        if "temperature" in state:
            self._color_temp = color_temperature_kelvin_to_mired(state["temperature"])
            self._attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif "hue" in state and "saturation" in state:
            hue = state["hue"] / 65535 * 360
            saturation = state["saturation"] / 65535 * 100
            self._hs_color = (hue, saturation)
            self._attr_supported_color_modes = {ColorMode.HS, ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.HS
        elif "lightness" in state:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

    async def _async_update_ha_state(self):
        """Update Home Assistant state and clear pending update flag."""
        await asyncio.sleep(1)  # Short delay to allow API to process the change
        self._pending_update = False
        await self.coordinator.async_request_refresh()
