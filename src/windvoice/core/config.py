import os
import tomllib
import tomli_w
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class LiteLLMConfig:
    api_key: str
    api_base: str
    key_alias: str
    model: str = "whisper-1"


@dataclass
class AppConfig:
    hotkey: str = "ctrl+shift+space"
    audio_device: str = "default"
    sample_rate: int = 44100


@dataclass
class UIConfig:
    theme: str = "dark"
    window_position: str = "center"
    show_tray_notifications: bool = True


@dataclass
class WindVoiceConfig:
    litellm: LiteLLMConfig
    app: AppConfig
    ui: UIConfig


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".windvoice"
        self.config_file = self.config_dir / "config.toml"
        self._config: Optional[WindVoiceConfig] = None

    def ensure_config_dir(self):
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self) -> WindVoiceConfig:
        if self._config:
            return self._config

        self.ensure_config_dir()

        if not self.config_file.exists():
            self._create_default_config()

        try:
            with open(self.config_file, "rb") as f:
                config_data = tomllib.load(f)
            
            self._config = WindVoiceConfig(
                litellm=LiteLLMConfig(**config_data.get("litellm", {})),
                app=AppConfig(**config_data.get("app", {})),
                ui=UIConfig(**config_data.get("ui", {}))
            )
            
            return self._config
            
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")

    def _create_default_config(self):
        default_config = {
            "litellm": {
                "api_key": "",
                "api_base": "",
                "key_alias": "",
                "model": "whisper-1"
            },
            "app": {
                "hotkey": "ctrl+shift+space",
                "audio_device": "default", 
                "sample_rate": 44100
            },
            "ui": {
                "theme": "dark",
                "window_position": "center",
                "show_tray_notifications": True
            }
        }

        with open(self.config_file, "wb") as f:
            tomli_w.dump(default_config, f)

    def save_config(self, config: WindVoiceConfig):
        self.ensure_config_dir()
        
        config_data = {
            "litellm": {
                "api_key": config.litellm.api_key,
                "api_base": config.litellm.api_base,
                "key_alias": config.litellm.key_alias,
                "model": config.litellm.model
            },
            "app": {
                "hotkey": config.app.hotkey,
                "audio_device": config.app.audio_device,
                "sample_rate": config.app.sample_rate
            },
            "ui": {
                "theme": config.ui.theme,
                "window_position": config.ui.window_position,
                "show_tray_notifications": config.ui.show_tray_notifications
            }
        }

        with open(self.config_file, "wb") as f:
            tomli_w.dump(config_data, f)
        
        self._config = config

    def validate_config(self) -> bool:
        config = self.load_config()
        
        if not config.litellm.api_key:
            return False
        if not config.litellm.api_base:
            return False
        if not config.litellm.key_alias:
            return False
            
        return True

    def get_config_status(self) -> dict:
        try:
            config = self.load_config()
            return {
                "config_exists": True,
                "api_key_configured": bool(config.litellm.api_key),
                "api_base_configured": bool(config.litellm.api_base),
                "key_alias_configured": bool(config.litellm.key_alias),
                "config_file_path": str(self.config_file)
            }
        except Exception:
            return {
                "config_exists": False,
                "api_key_configured": False,
                "api_base_configured": False,
                "key_alias_configured": False,
                "config_file_path": str(self.config_file)
            }


class ConfigError(Exception):
    pass