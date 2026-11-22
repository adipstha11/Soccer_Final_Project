"""HTTP client with rate limiting, retries with exponential backoff, and a
write-once on-disk raw cache. Raw files are never overwritten once saved."""
from __future__ import annotations

import gzip
import json
import logging
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

log = logging.getLogger(__name__)


class Client:
    def __init__(self, delay: float = config.REQUEST_DELAY):
        self.delay = delay
        self._last = 0.0
        self.s = requests.Session()
        retry = Retry(total=5, backoff_factor=1.5,
                      status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=("GET",), respect_retry_after_header=True)
        self.s.mount("https://", HTTPAdapter(max_retries=retry))
        self.s.mount("http://", HTTPAdapter(max_retries=retry))
        self.s.headers["User-Agent"] = config.USER_AGENT
        self.n_requests = 0

    def _throttle(self):
        wait = self.delay - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()

    def get_bytes(self, url: str, params: dict | None = None) -> bytes:
        self._throttle()
        r = self.s.get(url, params=params, timeout=60)
        self.n_requests += 1
        r.raise_for_status()
        return r.content

    def get_json(self, url: str, params: dict | None = None) -> dict:
        return json.loads(self.get_bytes(url, params))

    # ---------- cached variants ----------
    def cached_json(self, url: str, path: Path, params: dict | None = None,
                    cache_if=lambda d: True, gz: bool = False) -> dict:
        """Return JSON from `path` if present; otherwise download, and save it
        (write-once) only if `cache_if(data)` is True."""
        if path.exists():
            raw = path.read_bytes()
            return json.loads(gzip.decompress(raw) if gz else raw)
        data = self.get_json(url, params)
        if cache_if(data):
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(data, ensure_ascii=False).encode()
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(gzip.compress(payload) if gz else payload)
            tmp.rename(path)
        return data

    def cached_file(self, url: str, path: Path, refresh: bool = False) -> Path:
        """Download a file once. With refresh=True a NEW dated copy is written
        alongside (old raw snapshots are never overwritten)."""
        if path.exists() and not refresh:
            return path
        if path.exists() and refresh:
            stamp = time.strftime("%Y%m%d")
            path = path.with_name(f"{path.stem}__{stamp}{path.suffix}")
            if path.exists():
                return path
        content = self.get_bytes(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        log.info("downloaded %s -> %s (%d bytes)", url, path, len(content))
        return path
