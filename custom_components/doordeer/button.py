"""Doordeer Button entity — one-tap unlock."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DoordeerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: DoordeerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DoordeerUnlockButton(coordinator, entry)])


class DoordeerUnlockButton(CoordinatorEntity[DoordeerCoordinator], ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Unlock Door"
    _attr_icon = "mdi:door-open"

    def __init__(self, coordinator: DoordeerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_unlock_button"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.device_ip)},
            "name": "Doordeer Intercom",
            "manufacturer": "doordeer smart Inc",
            "model": "Video Intercom",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None and self.coordinator.data.connected

    async def async_press(self) -> None:
        await self.coordinator.unlock()
