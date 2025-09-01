#!/usr/bin/env python3
"""
Setup script to initialize WindVoice configuration with LiteLLM credentials.
This script creates the initial config.toml file in ~/.windvoice/
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from windvoice.core.config import ConfigManager, WindVoiceConfig, LiteLLMConfig, AppConfig, UIConfig

def main():
    print("WindVoice Configuration Setup")
    print("=" * 40)
    print("Please provide your Thomson Reuters LiteLLM credentials:\n")
    
    # Get LiteLLM credentials from user
    api_key = input("API Key (sk-xxxxx): ").strip()
    api_base = input("API Base URL (https://...): ").strip()
    key_alias = input("Key Alias (your.email@...): ").strip()
    
    # Validate inputs
    if not api_key or not api_base or not key_alias:
        print("Error: All fields are required!")
        sys.exit(1)
    
    if not api_key.startswith("sk-"):
        print("Error: API Key should start with 'sk-'")
        sys.exit(1)
    
    if not api_base.startswith("https://"):
        print("Error: API Base should start with 'https://'")
        sys.exit(1)
    
    config_manager = ConfigManager()
    
    # Create configuration with user-provided credentials
    config = WindVoiceConfig(
        litellm=LiteLLMConfig(
            api_key=api_key,
            api_base=api_base,
            key_alias=key_alias,
            model="whisper-1"
        ),
        app=AppConfig(
            hotkey="ctrl+shift+space",
            audio_device="default",
            sample_rate=44100
        ),
        ui=UIConfig(
            theme="dark",
            window_position="center",
            show_tray_notifications=True
        )
    )
    
    try:
        config_manager.save_config(config)
        print(f"\nConfiguration saved to: {config_manager.config_file}")
        print("LiteLLM credentials configured:")
        print(f"   - API Base: {config.litellm.api_base}")
        print(f"   - Key Alias: {config.litellm.key_alias}")
        print(f"   - Model: {config.litellm.model}")
        print(f"Hotkey set to: {config.app.hotkey}")
        print("\nWindVoice is ready! Run: python main.py")
        
    except Exception as e:
        print(f"Failed to save configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()