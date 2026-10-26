"""Shared HTTP, retry, and on-disk cache support for environmental clients."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)
USER_AGENT = "shark-attacks-collector/1.0 (educational research; contact: project maintainer)"


@dataclass
class RequestStats:
    api_calls: int = 0
    cache_hits: int = 0
    failures: int = 0
    retries: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "failures": self.failures,
            "retries": self.retries,
        }


def request_text(
    url: str,
    cache_dir: Path,
    stats: RequestStats,
    *,
    timeout: float = 30,
    retries: int = 3,
    pause_seconds: float = 0.25,
) -> str:
    """Fetch a URL once, retry transient failures, and cache the response body."""
    cache_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_path = cache_dir / f"{cache_key}.json"
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Ignoring invalid environmental cache entry: %s", cache_path)
        else:
            if cached.get("url") == url and isinstance(cached.get("body"), str):
                stats.cache_hits += 1
                return cached["body"]

    if retries < 1:
        raise ValueError("retries must be at least one")

    request = Request(url, headers={"Accept": "application/json,text/csv", "User-Agent": USER_AGENT})
    for attempt in range(retries):
        stats.api_calls += 1
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(
                    {
                        "url": url,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "body": body,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            time.sleep(pause_seconds)
            return body
        except (HTTPError, URLError, TimeoutError, OSError):
            if attempt + 1 == retries:
                stats.failures += 1
                LOGGER.exception("Environmental API request failed after %d attempts", retries)
                raise
            stats.retries += 1
            time.sleep(pause_seconds * (2**attempt))

    raise RuntimeError("unreachable retry state")
