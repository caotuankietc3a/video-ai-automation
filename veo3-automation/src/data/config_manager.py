import os
import json
from typing import Dict, Any, Optional
from ..config.constants import BASE_DIR

CONFIG_FILE = os.path.join(BASE_DIR, "data", "config.json")

class ConfigManager:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self._ensure_config_file()
        self.load()
    
    def _ensure_config_file(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        if not os.path.exists(CONFIG_FILE):
            self.config = self._default_config()
            self.save()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "api_keys": {
                "gemini": "",
                "openai": "",
                "anthropic": "",
                "local_api_url": "http://localhost:11434"
            },
            "default_model": "gemini",
            "default_style": "3d_Pixar",
            "default_duration": 120,
            "default_veo_profile": "VEO3 ULTRA",
            "default_aspect_ratio": "Khổ ngang (16:9)",
            "auto_update_interval": 20,
            "video_import_source": "local_and_url",
            "video_save_location": os.path.join(BASE_DIR, "data", "outputs"),
            "browser_automation": {
                "headless": False,
                "timeout": 30000,
                "channel": "chrome"
            },
            "content_generation": {
                "use_browser": True,
                "url": "https://gemini.google.com/app"
            },
            "video_analysis": {
                "use_browser": True,
                "url": "https://gemini.google.com/app"
            },
            "gemini_account": {
                "email": "jonathancacf@vinh.epstore.tech",
                "password": "Donchal03@@"
            }
        }
    
    def load(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()
            self.save()
    
    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    def get_api_key(self, provider: str) -> str:
        return self.get(f"api_keys.{provider}", "")
    
    def set_api_key(self, provider: str, key: str):
        self.set(f"api_keys.{provider}", key)

config_manager = ConfigManager()

