import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from config.settings import get_settings


class FileCache:
    _stats: dict[str, dict[str, int]] = {}

    def __init__(self, namespace: str = "default"):
        settings = get_settings()
        self.ttl = settings.cache_ttl_seconds
        self.cache_dir = Path(settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.namespace = namespace
        if namespace not in self._stats:
            self._stats[namespace] = {"hits": 0, "misses": 0}

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()}.json"

    def get(self, key: str) -> Any | None:
        p = self._path(key)
        if not p.exists():
            self._stats[self.namespace]["misses"] += 1
            return None
        payload = json.loads(p.read_text(encoding="utf-8"))
        if time.time() - payload["ts"] > self.ttl:
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
            self._stats[self.namespace]["misses"] += 1
            return None
        self._stats[self.namespace]["hits"] += 1
        return payload["value"]

    def set(self, key: str, value: Any) -> None:
        p = self._path(key)
        p.write_text(json.dumps({"ts": time.time(), "value": value}), encoding="utf-8")

    def invalidate(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            os.remove(p)

    def stats(self) -> dict:
        hits = self._stats[self.namespace]["hits"]
        misses = self._stats[self.namespace]["misses"]
        total = hits + misses
        hit_rate = (hits / total) if total else 0.0
        return {"hits": hits, "misses": misses, "hit_rate": round(hit_rate, 3)}
