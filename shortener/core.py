"""Shortener domain."""
import hashlib
from urllib.parse import urlparse


class Shortener:
    def __init__(self) -> None:
        self._urls: dict[str, str] = {}
        self.visits: dict[str, int] = {}

    def shorten(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url!r}")
        code = hashlib.sha256(url.encode()).hexdigest()[:6]
        self._urls[code] = url
        self.visits.setdefault(code, 0)
        return code

    def resolve(self, code: str) -> str:
        url = self._urls[code]
        self.visits[code] += 1
        return url
