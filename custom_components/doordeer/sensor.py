"""Doordeer Sensor entities."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    async_add_entities([
        DoordeerConnectionSensor(coordinator, entry),
        DoordeerRtspSensor(coordinator, entry),
        DoordeerLogCountSensor(coordinator, entry),
    ])


def _device_info(coordinator: DoordeerCoordinator) -> dict:
    return {
        "identifiers": {(DOMAIN, coordinator.device_ip)},
        "name": "Doordeer Intercom",
        "manufacturer": "doordeer smart Inc",
        "model": "Video Intercom",
    }


class DoordeerConnectionSensor(CoordinatorEntity[DoordeerCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Connection Status"
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connection"

    @property
    def device_info(self): return _device_info(self.coordinator)

    @property
    def native_value(self) -> str:
        if self.coordinator.data is None:
            return "unavailable"
        return "connected" if self.coordinator.data.connected else "disconnected"

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data
        if not d:
            return {}
        return {"last_seen": d.last_seen, "device_ip": self.coordinator.device_ip}


class DoordeerRtspSensor(CoordinatorEntity[DoordeerCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "RTSP Stream"
    _attr_icon = "mdi:video-wireless"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_rtsp"

    @property
    def device_info(self): return _device_info(self.coordinator)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.rtsp_main if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data
        if not d:
            return {}
        return {
            "rtsp_sub": d.rtsp_sub,
            "video_format": d.video_format,
            "audio_format": d.audio_format,
        }


class DoordeerLogCountSensor(CoordinatorEntity[DoordeerCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Access Log Entries"
    _attr_icon = "mdi:clipboard-list"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_log_count"

    @property
    def device_info(self): return _device_info(self.coordinator)

    @property
    def native_value(self) -> int:
        return len(self.coordinator.get_log(limit=10000))
