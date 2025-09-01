#!/usr/bin/env python3
"""
Test the Settings UI independently to debug the LiteLLM test button
"""

import sys
sys.path.insert(0, 'src')

import asyncio
import tkinter as tk
import customtkinter as ctk
from windvoice.core.config import ConfigManager
from windvoice.services.audio import AudioRecorder
from windvoice.ui.settings import SettingsWindow
from windvoice.utils.logging import setup_logging

def test_settings_window():
    """Test the settings window independently"""
    
    print("=== Settings Window Test ===\n")
    
    # Setup logging
    logger = setup_logging("DEBUG", True)  # Console + file
    
    try:
        # Initialize Tkinter
        print("Initializing UI...")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create hidden root window
        root = ctk.CTk()
        root.withdraw()  # Hide main window
        
        # Create config manager and audio recorder
        print("Setting up services...")
        config_manager = ConfigManager()
        audio_recorder = AudioRecorder()
        
        # Create settings window
        print("Creating settings window...")
        settings = SettingsWindow(config_manager, audio_recorder)
        
        # Show settings window
        print("Showing settings window...")
        settings.show()
        
        print("\n📋 INSTRUCTIONS:")
        print("1. The settings window should now be visible")
        print("2. Enter your LiteLLM credentials:")
        print("   - API Base: https://your-proxy.com")
        print("   - API Key: sk-your-key-here") 
        print("   - Key Alias: your-username")
        print("3. Click 'Test API Connection' button")
        print("4. Watch the console for detailed logs")
        print("5. Close the window when done")
        print("-" * 60)
        
        # Run the UI event loop
        print("Starting UI event loop - check the console for logs...")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error during settings test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_settings_window()