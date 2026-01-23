from __future__ import annotations

import json
import os
from typing import Any, Dict

from .constants import CONFIG_FILE, BASE_DIR


class ConfigManager:
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self._ensure_config_file()
        self.load()

    def _ensure_config_file(self) -> None:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        if not CONFIG_FILE.exists():
            self.config = self._default_config()
            self.save()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "freepik_account": {
                "email": "",
                "password": "",
            },
            "browser_automation": {
                "headless": False,
                "timeout": 30000,
                "channel": "chrome",
            },
            "video_generator": {
                "url": "https://www.freepik.com/",
            },
            "outputs": {
                "dir": str(BASE_DIR / "data" / "outputs"),
            },
        }

    def load(self) -> None:
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                self.config = json.load(file)
        else:
            self.config = self._default_config()
            self.save()

    def save(self) -> None:
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any | None = None) -> Any:
        keys = key.split(".")
        value: Any = self.config
        for current_key in keys:
            if isinstance(value, dict):
                value = value.get(current_key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        config: Dict[str, Any] = self.config
        for current_key in keys[:-1]:
            if current_key not in config or not isinstance(config[current_key], dict):
                config[current_key] = {}
            nested = config[current_key]
            assert isinstance(nested, dict)
            config = nested
        config[keys[-1]] = value
        self.save()


config_manager = ConfigManager()

