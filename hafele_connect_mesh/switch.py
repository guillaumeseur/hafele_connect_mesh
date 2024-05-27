import logging
import aiohttp  # Ensure aiohttp is imported
from homeassistant.components.switch import SwitchEntity

from . import DOMAIN, HafeleConnectMeshDevice

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Häfele Connect Mesh switches from a config entry."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    api_key = config["api_key"]
    devices = config["devices"]

    switches = []
    for device in devices:
        if device["type"] not in ["com.haefele.led.white.strip", "com.haefele.led.rgb", "com.haefele.led.white", "com.haefele.led.multiwhite.2700K"]:
            switches.append(HafeleConnectMeshSwitch(device, api_key))

    async_add_entities(switches, True)

class HafeleConnectMeshSwitch(HafeleConnectMeshDevice, SwitchEntity):
    """Representation of a Häfele Connect Mesh switch."""

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._set_power("on")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._set_power("off")

    async def _set_power(self, power):
        """Set the power state of the switch."""
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            "power": power,
            "uniqueId": self.unique_id,
            "acknowledged": True,
            "retries": 0,
            "timeout_ms": 10000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put('https://cloud.connect-mesh.io/api/core/devices/power', headers=headers, json=payload) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set power for device %s: %s", self.unique_id, response.status)
                else:
                    self._state = power == "on"
                    self.async_write_ha_state()
