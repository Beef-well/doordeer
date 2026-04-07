"""Doordeer Smart Intercom — Home Assistant Custom Integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN, PLATFORMS, CONF_DEVICE_IP, CONF_DEVICE_PORT, CONF_RC4_KEY
from .coordinator import DoordeerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Doordeer from a config entry."""
    coordinator = DoordeerCoordinator(
        hass=hass,
        device_ip=entry.data[CONF_DEVICE_IP],
        device_port=entry.data[CONF_DEVICE_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        rc4_key=entry.data[CONF_RC4_KEY],
    )

    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ── Services ──────────────────────────────────────────────────────
    async def handle_unlock(call: ServiceCall) -> None:
        await coordinator.unlock()

    async def handle_change_password(call: ServiceCall) -> None:
        await coordinator.change_password(
            new_password=call.data["password"],
            username=call.data.get("username"),
        )

    hass.services.async_register(DOMAIN, "unlock", handle_unlock)
    hass.services.async_register(DOMAIN, "change_password", handle_change_password)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: DoordeerCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok
