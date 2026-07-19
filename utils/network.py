from __future__ import annotations

from urllib.parse import urlparse

_PRIVATE_PREFIXES = (
    "10.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.",
    "192.168.", "127.", "0.", "169.254.",
)

_LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname or ""
    if host in _LOOPBACK_NAMES:
        return False
    for prefix in _PRIVATE_PREFIXES:
        if host.startswith(prefix):
            return False
    return True
