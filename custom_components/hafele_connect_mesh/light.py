import logging
import aiohttp
import colorsys  # Import colorsys to convert RGB to HSL
from homeassistant.components.light import (
    LightEntity, ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_HS_COLOR
)
from homeassistant.util.color import color_hs_to_RGB

from . import DOMAIN, HafeleConnectMeshDevice

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Häfele Connect Mesh lights from a config entry."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    api_key = config["api_key"]
    devices = config["devices"]

    lights = []
    for device in devices:
        if device["type"] in ["com.haefele.led.white.strip", "com.haefele.led.rgb", "com.haefele.led.white", "com.haefele.led.multiwhite.2700K"]:
            lights.append(HafeleConnectMeshLight(device, api_key))

    async_add_entities(lights, True)

class HafeleConnectMeshLight(HafeleConnectMeshDevice, LightEntity):
    """Representation of a Häfele Connect Mesh light."""

    def __init__(self, device, api_key):
        """Initialize the light."""
        super().__init__(device, api_key)
        self._hs_color = None
        self._brightness = None

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self):
        """Return the hue and saturation color value [float, float]."""
        return self._hs_color

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self._set_power("on", **kwargs)

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._set_power("off")

    async def _set_power(self, power, **kwargs):
        """Set the power state of the light."""
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json'
        }
        
        if power == "on":
            if ATTR_BRIGHTNESS in kwargs:
                brightness = kwargs[ATTR_BRIGHTNESS] / 255.0
                payload = {
                    "lightness": brightness,
                    "uniqueId": self.unique_id,
                    "acknowledged": True,
                    "retries": 0,
                    "timeout_ms": 10000
                }
                url = 'https://cloud.connect-mesh.io/api/core/devices/lightness'
            elif ATTR_HS_COLOR in kwargs:
                hs_color = kwargs[ATTR_HS_COLOR]
                hue = hs_color[0] / 360.0  # Convert hue to 0-1 range
                saturation = hs_color[1] / 100.0  # Convert saturation to 0-1 range
                payload = {
                    "hue": hue,
                    "saturation": saturation,
                    "lightness": self.brightness / 255.0 if self.brightness else 1.0,
                    "uniqueId": self.unique_id,
                    "acknowledged": True,
                    "retries": 0,
                    "timeout_ms": 10000
                }
                url = 'https://cloud.connect-mesh.io/api/core/devices/hsl'
            else:
                payload = {
                    "power": power,
                    "uniqueId": self.unique_id,
                    "acknowledged": True,
                    "retries": 0,
                    "timeout_ms": 10000
                }
                url = 'https://cloud.connect-mesh.io/api/core/devices/power'
        else:
            payload = {
                "power": power,
                "uniqueId": self.unique_id,
                "acknowledged": True,
                "retries": 0,
                "timeout_ms": 10000
            }
            url = 'https://cloud.connect-mesh.io/api/core/devices/power'
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set power for device %s: %s", self.unique_id, response.status)
                else:
                    self._state = power == "on"
                    if ATTR_BRIGHTNESS in kwargs:
                        self._brightness = kwargs[ATTR_BRIGHTNESS]
                    if ATTR_HS_COLOR in kwargs:
                        self._hs_color = kwargs[ATTR_HS_COLOR]
                    self.async_write_ha_state()
