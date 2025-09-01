#!/usr/bin/env python3
"""
Test LiteLLM button independently with polling-based UI updates
"""

import sys
sys.path.insert(0, 'src')

import tkinter as tk
import customtkinter as ctk
from windvoice.core.config import ConfigManager
from windvoice.services.audio import AudioRecorder
from windvoice.ui.settings import SettingsWindow
from windvoice.utils.logging import setup_logging

def test_litellm_button():
    """Test the LiteLLM button with new polling system"""
    
    print("=== LiteLLM Button Test with Polling System ===\n")
    
    # Setup logging
    logger = setup_logging("DEBUG", False)  # Console only for this test
    
    try:
        # Initialize UI
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        root = ctk.CTk()
        root.withdraw()  # Hide main window
        
        # Create services
        config_manager = ConfigManager()
        audio_recorder = AudioRecorder()
        
        # Create settings window
        settings = SettingsWindow(config_manager, audio_recorder)
        settings.show()
        
        print("\n📋 INSTRUCTIONS FOR TESTING:")
        print("1. Fill in your LiteLLM credentials:")
        print("   - API Base: https://litellm.int.thomsonreuters.com")
        print("   - API Key: [your Thomson Reuters key]")
        print("   - Key Alias: [your alias]")
        print("2. Click 'Test API Connection' button")
        print("3. Watch the console for detailed polling logs")
        print("4. The button should:")
        print("   - Change to 'Testing...'")
        print("   - Show 'Connection OK' or 'Test Failed'")
        print("   - Show a popup dialog with results")
        print("   - Auto-reset to 'Test API Connection'")
        print("5. Close the window when done")
        print("-" * 70)
        print("🔍 Expected log flow:")
        print("   [UI] → [THREAD] → [TEST] → [POLL] → [UI] Success/Error")
        print("-" * 70)
        
        # Run event loop
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_litellm_button()