#!/usr/bin/env python3
"""
WindVoice-Windows Main Entry Point

Native Windows voice dictation application with global hotkey support.
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from windvoice.core.app import main
from windvoice.core.config import ConfigManager

def create_emergency_config():
    """Create a template configuration for emergency setup"""
    config_manager = ConfigManager()
    config_manager.ensure_config_dir()
    
    template_content = """# WindVoice-Windows Configuration
# Please fill in your LiteLLM credentials below and restart the application

[litellm]
api_key = "sk-your-litellm-api-key"  # Replace with your actual API key
api_base = "https://your-proxy.thomsonreuters.com"  # Replace with your proxy URL
key_alias = "your.email@company.com"  # Replace with your identifier
model = "whisper-1"

[app]
hotkey = "ctrl+shift+space"
audio_device = "default"
sample_rate = 44100

[ui]
theme = "dark"
window_position = "center"
show_tray_notifications = true
"""
    
    try:
        with open(config_manager.config_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # Also create the setup completion marker
        setup_marker = config_manager.config_dir / ".setup_completed"
        setup_marker.touch()
        
        print(f"[SUCCESS] Emergency configuration template created at:")
        print(f"   {config_manager.config_file}")
        print(f"\n[SETUP] Please edit the file and replace the placeholder values with your actual:")
        print(f"   - LiteLLM API key (starts with 'sk-')")
        print(f"   - LiteLLM proxy URL")
        print(f"   - Your username/email for tracking")
        print(f"\n[RESTART] After editing, restart WindVoice-Windows to use the new configuration.")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to create configuration template: {e}")
        return False

def main_with_args():
    parser = argparse.ArgumentParser(description="WindVoice-Windows voice dictation application")
    parser.add_argument("--create-config", action="store_true", 
                       help="Create emergency configuration template and exit")
    parser.add_argument("--check-config", action="store_true",
                       help="Check configuration status and exit")
    
    args = parser.parse_args()
    
    if args.create_config:
        success = create_emergency_config()
        sys.exit(0 if success else 1)
    
    if args.check_config:
        config_manager = ConfigManager()
        setup_marker = config_manager.config_dir / ".setup_completed"
        
        print("WindVoice-Windows Configuration Status")
        print("=" * 40)
        print(f"Config directory: {config_manager.config_dir}")
        print(f"Config file: {'[OK] Exists' if config_manager.config_exists() else '[MISSING]'}")
        print(f"Setup completed: {'[OK] Yes' if setup_marker.exists() else '[NO] Missing'}")
        
        if config_manager.config_exists():
            try:
                config = config_manager.load_config()
                creds_ok = all([config.litellm.api_key, config.litellm.api_base, config.litellm.key_alias])
                print(f"Valid credentials: {'[OK] Yes' if creds_ok else '[ERROR] No (empty fields)'}")
            except Exception as e:
                print(f"Config validation: [ERROR] - {e}")
        
        sys.exit(0)
    
    # Normal application startup
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWindVoice stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"WindVoice failed to start: {e}")
        print(f"\n[TIP] Try running with --create-config to set up configuration manually")
        sys.exit(1)

if __name__ == "__main__":
    main_with_args()