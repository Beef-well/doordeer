"""Doordeer Camera entity — RTSP stream + JPEG snapshot direct from device."""
from __future__ import annotations

import logging

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DoordeerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: DoordeerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DoordeerCamera(coordinator, entry)])


class DoordeerCamera(CoordinatorEntity[DoordeerCoordinator], Camera):
    _attr_has_entity_name = True
    _attr_name = "Doorbell Camera"
    _attr_icon = "mdi:doorbell-video"
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, coordinator: DoordeerCoordinator, entry: ConfigEntry) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}_camera"

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

    async def async_camera_image(self, width=None, height=None) -> bytes | None:
        return await self.coordinator.get_snapshot()

    async def stream_source(self) -> str | None:
        if self.coordinator.data:
            return self.coordinator.data.rtsp_main
        return None
