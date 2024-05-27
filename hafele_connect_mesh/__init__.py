import aiohttp  # Ensure aiohttp is imported
from homeassistant.helpers.entity import Entity
from homeassistant.components.light import SUPPORT_BRIGHTNESS, SUPPORT_COLOR, SUPPORT_COLOR_TEMP, LightEntity
from homeassistant.const import ATTR_SUPPORTED_FEATURES

DOMAIN = "hafele_connect_mesh"

async def async_setup(hass, config):
    """Set up the Häfele Connect Mesh component."""
    return True

async def async_setup_entry(hass, entry):
    """Set up Häfele Connect Mesh from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "switch"))
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "light"))

    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "light")
    hass.data[DOMAIN].pop(entry.entry_id)

    return True

class HafeleConnectMeshDevice(Entity):
    """Representation of a Häfele Connect Mesh device."""

    def __init__(self, device, api_key):
        """Initialize the device."""
        self._device = device
        self._api_key = api_key
        self._state = None
        self._brightness = None
        self._supported_features = 0

        device_type = device["type"]
        if device_type in ["com.haefele.led.white.strip", "com.haefele.led.rgb", "com.haefele.led.white", "com.haefele.led.multiwhite.2700K"]:
            self._supported_features |= SUPPORT_BRIGHTNESS
        if device_type == "com.haefele.led.rgb":
            self._supported_features |= SUPPORT_COLOR
        if device_type == "com.haefele.led.multiwhite.2700K":
            self._supported_features |= SUPPORT_COLOR_TEMP

    @property
    def name(self):
        """Return the name of the device."""
        return self._device["name"]

    @property
    def unique_id(self):
        """Return the unique ID of the device."""
        return self._device["uniqueId"]

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self._state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def supported_features(self):
        """Return the supported features."""
        return self._supported_features

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        await self._set_power("on", **kwargs)

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        await self._set_power("off")

    async def _set_power(self, power, **kwargs):
        """Set the power state of the device."""
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
        
        if "brightness" in kwargs:
            payload["lightness"] = kwargs["brightness"] / 255.0
        
        async with aiohttp.ClientSession() as session:
            async with session.put('https://cloud.connect-mesh.io/api/core/devices/power', headers=headers, json=payload) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set power for device %s: %s", self.unique_id, response.status)
                else:
                    self._state = power == "on"
                    if "brightness" in kwargs:
                        self._brightness = kwargs["brightness"]
                    self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for this device."""
        # Implement the code to update the state of the device if needed
