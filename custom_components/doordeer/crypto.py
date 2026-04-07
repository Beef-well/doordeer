"""RC4 + Base64 encoding as required by the doordeer LAN API."""
from __future__ import annotations

import base64
import json
from typing import Any


def rc4_crypt(key: str, data: str) -> bytes:
    """RC4 stream cipher — symmetric, used for both encrypt and decrypt."""
    key_bytes = key.encode("utf-8")
    data_bytes = data.encode("utf-8")

    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key_bytes[i % len(key_bytes)]) % 256
        S[i], S[j] = S[j], S[i]

    i = j = 0
    out = []
    for byte in data_bytes:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(byte ^ S[(S[i] + S[j]) % 256])

    return bytes(out)


def build_body(key: str, payload: dict[str, Any]) -> dict[str, str]:
    """Return {"jsondata": "<rc4+base64 encoded payload>"} ready to POST."""
    raw = json.dumps(payload, separators=(",", ":"))
    encrypted = rc4_crypt(key, raw)
    encoded = base64.b64encode(encrypted).decode("utf-8")
    return {"jsondata": encoded}
