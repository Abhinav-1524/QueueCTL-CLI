import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

DEFAULTS = {
    "max_retries": 4,
    "backoff_base": 2,
    "worker_count": 2,
    "job_timeout": 45
}


class Config:
    """simple JSON-based config handler"""

    def __init__(self, path: Path = CONFIG_FILE):
        self.path = path
        if not self.path.exists():
            self._write(DEFAULTS)

    # ------------------------
    # basic I/O
    # ------------------------
    def _read(self) -> dict:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULTS.copy()

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ------------------------
    # public API
    # ------------------------
    def all(self) -> dict:
        """return all config values"""
        return self._read()

    def get(self, key: str, default=None):
        """fetch key"""
        return self._read().get(key, default)

    def set(self, key: str, value):
        """update key"""
        data = self._read()
        data[key] = value
        self._write(data)

    def restore_defaults(self):
        """reset to defaults"""
        self._write(DEFAULTS)

    # ------------------------
    # shortcuts
    # ------------------------
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, val):
        self.set(key, val)
