from __future__ import annotations

import base64
import hmac
import secrets
import struct
import time
from hashlib import sha1
from urllib.parse import quote


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def provisioning_uri(email: str, secret: str, issuer: str = "SentinelX") -> str:
    label = quote(f"{issuer}:{email}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    candidate = "".join(char for char in code if char.isdigit())
    if len(candidate) != 6:
        return False
    current = int(time.time() // 30)
    return any(hmac.compare_digest(candidate, _totp(secret, current + offset)) for offset in range(-window, window + 1))


def _totp(secret: str, counter: int) -> str:
    padding = "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(secret + padding, casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{code % 1_000_000:06d}"
