import requests
import voluptuous as vol
import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@callback
def configured_instances(hass):
    return set(entry.data.get("name") for entry in hass.config_entries.async_entries(DOMAIN))

class HafeleConnectMeshConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.api_key = user_input["api_key"]
            return await self.async_step_networks()
        
        schema = vol.Schema({
            vol.Required("api_key"): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )

    async def async_step_networks(self, user_input=None):
        errors = {}
        headers = {
            'accept': '*/*',
            'Authorization': f'Bearer {self.api_key}'
        }

        def get_networks():
            try:
                _LOGGER.debug("Trying to connect to the API with the provided API key")
                response = requests.get('https://cloud.connect-mesh.io/api/core/networks', headers=headers)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as req_err:
                _LOGGER.error("Request exception occurred: %s", req_err)
                raise

        try:
            networks = await self.hass.async_add_executor_job(get_networks)
            _LOGGER.debug("API response received: %s", networks)

            if not networks:
                _LOGGER.warning("No networks found")
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({vol.Required("api_key"): str}),
                    errors={"base": "no_networks"},
                    description_placeholders={"networks": ""}
                )

            self.networks = {network["id"]: network["name"] for network in networks}
            network_options = {network["id"]: network["name"] for network in networks}

            schema = vol.Schema({
                vol.Required("network"): vol.In(network_options)
            })

            return self.async_show_form(
                step_id="select_network",
                data_schema=schema,
                description_placeholders={"networks": ", ".join(network_options.values())},
            )

        except requests.exceptions.RequestException:
            errors["base"] = "cannot_connect"
        except Exception as err:
            _LOGGER.error("Unexpected error occurred: %s", err)
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("api_key"): str}),
            errors=errors
        )

    async def async_step_select_network(self, user_input=None):
        if user_input is not None:
            self.network_id = user_input["network"]
            self.network_name = self.networks[self.network_id]
            return await self.async_step_devices()
        
        return self.async_abort(reason="no_network_selected")

    async def async_step_devices(self, user_input=None):
        errors = {}
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        def get_devices():
            try:
                _LOGGER.debug("Trying to get devices for the network: %s", self.network_name)
                response = requests.get('https://cloud.connect-mesh.io/api/core/devices', headers=headers)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as req_err:
                _LOGGER.error("Request exception occurred: %s", req_err)
                raise

        try:
            devices = await self.hass.async_add_executor_job(get_devices)
            _LOGGER.debug("API response for devices: %s", devices)

            self.devices = [device for device in devices if device['networkId'] == self.network_id]
            _LOGGER.debug("Filtered devices: %s", self.devices)

            if not self.devices:
                _LOGGER.warning("No devices found for the selected network")
                return self.async_show_form(
                    step_id="select_network",
                    data_schema=vol.Schema({
                        vol.Required("network"): vol.In({network_id: name for network_id, name in self.networks.items()})
                    }),
                    errors={"base": "no_devices"},
                    description_placeholders={"networks": self.network_name}
                )

            return self.async_create_entry(
                title=self.network_name,
                data={
                    "api_key": self.api_key,
                    "network_id": self.network_id,
                    "devices": self.devices
                }
            )

        except requests.exceptions.RequestException:
            errors["base"] = "cannot_connect"
        except Exception as err:
            _LOGGER.error("Unexpected error occurred: %s", err)
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="select_network",
            data_schema=vol.Schema({
                vol.Required("network"): vol.In({network_id: name for network_id, name in self.networks.items()})
            }),
            errors=errors,
            description_placeholders={"networks": self.network_name}
        )
