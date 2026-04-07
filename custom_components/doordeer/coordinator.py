"""
Doordeer DataUpdateCoordinator.
Owns the device session, token lifecycle, and all LAN API calls.
All entities read from this coordinator — one HTTP session, one token.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .crypto import build_body
from .const import (
    DOMAIN,
    TOKEN_LIFETIME,
    TOKEN_REFRESH_BEFORE,
    DEFAULT_PORT,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class DoordeerData:
    """Current state snapshot polled from the device."""
    connected: bool = False
    rtsp_main: Optional[str] = None
    rtsp_sub: Optional[str] = None
    video_format: Optional[str] = None
    audio_format: Optional[str] = None
    last_seen: float = 0.0


@dataclass
class AccessLogEntry:
    timestamp: float
    event: str
    source: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event": self.event,
            "source": self.source,
            "detail": self.detail,
        }


class DoordeerCoordinator(DataUpdateCoordinator[DoordeerData]):
    """Manages the doordeer device connection and exposes API methods to entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_ip: str,
        device_port: int,
        username: str,
        password: str,
        rc4_key: str,
    ) -> None:
        from datetime import timedelta
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.device_ip = device_ip
        self.device_port = device_port
        self.username = username
        self.password = password
        self.rc4_key = rc4_key

        self._base_url = f"http://{device_ip}:{device_port}"
        self._token: Optional[str] = None
        self._token_acquired: float = 0.0
        self._token_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_log: list[AccessLogEntry] = []

    # ------------------------------------------------------------------ #
    #  Session                                                             #
    # ------------------------------------------------------------------ #

    async def async_setup(self) -> None:
        """Create aiohttp session and perform first login."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        await self._login()

    async def async_shutdown(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    # ------------------------------------------------------------------ #
    #  DataUpdateCoordinator hook                                          #
    # ------------------------------------------------------------------ #

    async def _async_update_data(self) -> DoordeerData:
        """Called by HA every update_interval. Refresh token + fetch RTSP info."""
        try:
            await self._ensure_token()
            rtsp = await self._fetch_rtsp()
            data = DoordeerData(
                connected=self._token is not None,
                rtsp_main=rtsp.get("mainvideo") if rtsp else None,
                rtsp_sub=rtsp.get("subvideo") if rtsp else None,
                video_format=rtsp.get("videoformat") if rtsp else None,
                audio_format=rtsp.get("audioformat") if rtsp else None,
                last_seen=time.time(),
            )
            return data
        except ConfigEntryAuthFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Doordeer update failed: {err}") from err

    # ------------------------------------------------------------------ #
    #  Authentication                                                      #
    # ------------------------------------------------------------------ #

    async def _login(self) -> bool:
        payload = {
            "function": "login",
            "user": self.username,
            "password": self.password,
        }
        body = build_body(self.rc4_key, payload)
        try:
            async with self._session.post(
                f"{self._base_url}/login",
                json=body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json(content_type=None)
                if data.get("rescode") == "200":
                    self._token = data["token"]
                    self._token_acquired = time.monotonic()
                    _LOGGER.info("Doordeer: authenticated successfully")
                    self._log("auth", "integration", "Login OK")
                    return True
                _LOGGER.error("Doordeer: login failed — check username/password/rc4_key: %s", data)
                self._token = None
                return False
        except Exception as exc:
            _LOGGER.error("Doordeer: login exception: %s", exc)
            self._token = None
            return False

    async def _ensure_token(self) -> None:
        async with self._token_lock:
            age = time.monotonic() - self._token_acquired
            if self._token is None or age >= (TOKEN_LIFETIME - TOKEN_REFRESH_BEFORE):
                _LOGGER.debug("Doordeer: refreshing token (age=%.0fs)", age)
                await self._login()

    # ------------------------------------------------------------------ #
    #  API calls — used directly by entities                               #
    # ------------------------------------------------------------------ #

    async def unlock(self) -> bool:
        await self._ensure_token()
        if not self._token:
            return False
        try:
            async with self._session.post(
                f"{self._base_url}/openlock",
                params={"token": self._token},
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json(content_type=None)
                success = data.get("rescode") == "200"
                self._log(
                    "unlock_success" if success else "unlock_failed",
                    "integration",
                    str(data),
                )
                return success
        except Exception as exc:
            _LOGGER.error("Doordeer: unlock error: %s", exc)
            self._log("unlock_error", "integration", str(exc))
            return False

    async def get_snapshot(self) -> Optional[bytes]:
        await self._ensure_token()
        if not self._token:
            return None
        try:
            async with self._session.post(
                f"{self._base_url}/getpic",
                params={"token": self._token},
                headers={"Content-Type": "image/jpeg"},
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception as exc:
            _LOGGER.error("Doordeer: snapshot error: %s", exc)
        return None

    async def _fetch_rtsp(self) -> Optional[dict]:
        if not self._token:
            return None
        try:
            async with self._session.post(
                f"{self._base_url}/getrtsp",
                params={"token": self._token},
                headers={"Content-Type": "application/json"},
            ) as resp:
                return await resp.json(content_type=None)
        except Exception as exc:
            _LOGGER.error("Doordeer: RTSP fetch error: %s", exc)
        return None

    async def change_password(self, new_password: str, username: Optional[str] = None) -> bool:
        await self._ensure_token()
        if not self._token:
            return False
        payload = {
            "function": "setuserpassword",
            "user": username or self.username,
            "password": new_password,
        }
        body = build_body(self.rc4_key, payload)
        try:
            async with self._session.post(
                f"{self._base_url}/setting",
                params={"token": self._token},
                json=body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json(content_type=None)
                success = data.get("rescode") == "200"
                self._log(
                    "password_changed" if success else "password_change_failed",
                    "integration",
                    f"user={username or self.username}",
                )
                return success
        except Exception as exc:
            _LOGGER.error("Doordeer: change_password error: %s", exc)
        return False

    # ------------------------------------------------------------------ #
    #  Access log                                                          #
    # ------------------------------------------------------------------ #

    def _log(self, event: str, source: str, detail: str = "") -> None:
        self._access_log.append(
            AccessLogEntry(time.time(), event, source, detail)
        )

    def get_log(self, limit: int = 200) -> list[dict]:
        return [e.to_dict() for e in reversed(self._access_log[-limit:])]

    def prune_log(self, days: int = 30) -> None:
        cutoff = time.time() - (days * 86400)
        self._access_log = [e for e in self._access_log if e.timestamp >= cutoff]
