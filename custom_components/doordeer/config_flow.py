"""Config flow for Doordeer integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    CONF_DEVICE_IP,
    CONF_DEVICE_PORT,
    CONF_RC4_KEY,
)
from .crypto import build_body

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_IP): str,
    vol.Optional(CONF_DEVICE_PORT, default=DEFAULT_PORT): int,
    vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_RC4_KEY): str,
})


async def _test_connection(
    ip: str, port: int, username: str, password: str, rc4_key: str
) -> str | None:
    """Try to login. Returns None on success, error key string on failure."""
    url = f"http://{ip}:{port}/login"
    payload = {"function": "login", "user": username, "password": password}
    try:
        body = build_body(rc4_key, payload)
    except Exception:
        return "invalid_rc4_key"

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=8)
        ) as session:
            async with session.post(
                url,
                json=body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json(content_type=None)
                if data.get("rescode") == "200" and data.get("token"):
                    return None
                return "invalid_auth"
    except aiohttp.ClientConnectorError:
        return "cannot_connect"
    except Exception:
        return "unknown"


class DoordeerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Doordeer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            error = await _test_connection(
                ip=user_input[CONF_DEVICE_IP],
                port=user_input[CONF_DEVICE_PORT],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                rc4_key=user_input[CONF_RC4_KEY],
            )
            if error is None:
                await self.async_set_unique_id(
                    f"doordeer_{user_input[CONF_DEVICE_IP]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Doordeer @ {user_input[CONF_DEVICE_IP]}",
                    data=user_input,
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
