"""Doordeer Lock entity."""
from __future__ import annotations

from homeassistant.components.lock import LockEntity
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
    async_add_entities([DoordeerLock(coordinator, entry)])


class DoordeerLock(CoordinatorEntity[DoordeerCoordinator], LockEntity):
    _attr_has_entity_name = True
    _attr_name = "Door Lock"
    _attr_icon = "mdi:door-closed-lock"
    _attr_is_locked = True

    def __init__(self, coordinator: DoordeerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_lock"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.device_ip)},
            "name": "Doordeer Intercom",
            "manufacturer": "doordeer smart Inc",
            "model": "Video Intercom",
            "configuration_url": f"http://{self.coordinator.device_ip}:{self.coordinator.device_port}",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None and self.coordinator.data.connected

    async def async_unlock(self, **kwargs) -> None:
        await self.coordinator.unlock()

    async def async_lock(self, **kwargs) -> None:
        pass  # Hardware auto-relocks
