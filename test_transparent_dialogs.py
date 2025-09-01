#!/usr/bin/env python3
"""
Test script for transparent status dialogs
Tests the improved transparent and cursor-aware status dialogs
"""

import sys
import os
import time
import customtkinter as ctk
import tkinter as tk

# Add src to path to import WindVoice modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from windvoice.ui.status_dialog import StatusDialogManager, DialogState
    print("✅ Successfully imported StatusDialogManager")
except ImportError as e:
    print(f"❌ Failed to import StatusDialogManager: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_transparent_dialogs():
    """Test the transparent status dialogs"""
    print("🧪 Testing Transparent Status Dialogs")
    print("=" * 50)
    
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create main test window (hidden, just for tkinter loop)
    root = ctk.CTk()
    root.withdraw()  # Hide the main window
    root.title("Dialog Test Control")
    
    # Create status dialog manager
    dialog_manager = StatusDialogManager()
    
    def test_recording_dialog():
        """Test recording dialog with transparency and smart positioning"""
        print("📹 Testing Recording Dialog...")
        dialog_manager.show_recording()
        
        # Simulate audio levels for 3 seconds
        def simulate_audio():
            import math
            for frame in range(60):  # ~3 seconds at 20fps
                level = abs(math.sin(frame * 0.1)) * 0.8 + 0.1  # Simulate varying audio
                dialog_manager.update_audio_level(level)
                root.after(50)  # 20fps
                root.update()
                time.sleep(0.05)
        
        root.after(100, simulate_audio)
        root.after(3500, lambda: dialog_manager.show_processing())
    
    def test_processing_dialog():
        """Test processing dialog"""
        print("⚙️ Testing Processing Dialog...")
        # Processing will be shown automatically after recording
        root.after(2000, lambda: dialog_manager.show_success())
    
    def test_success_dialog():
        """Test success dialog"""
        print("✅ Testing Success Dialog...")
        # Success will be shown automatically and auto-hide
        root.after(2000, lambda: dialog_manager.show_error())
    
    def test_error_dialog():
        """Test error dialog"""
        print("❌ Testing Error Dialog...")
        # Error will be shown automatically and auto-hide
        root.after(3000, lambda: print("🎉 All tests completed! Dialog should auto-hide."))
    
    # Start the test sequence
    print("🚀 Starting dialog test sequence...")
    print("📍 Dialog should appear near your cursor on the active monitor")
    print("🎨 Dialog is transparent and should show content behind it")
    print("🖱️ You can drag the dialog around and right-click for options")
    print()
    
    # Start first test
    root.after(1000, test_recording_dialog)
    
    # Keep the test running
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    finally:
        if dialog_manager:
            dialog_manager.hide()
        print("🧹 Cleanup completed")

def test_positioning():
    """Test cursor-aware positioning"""
    print("\n🎯 Testing Cursor-Aware Positioning")
    print("=" * 50)
    print("📍 Move your cursor to different monitors/positions and press Enter")
    print("📦 Dialog should appear near cursor on the active monitor")
    print("⏭️ Press Enter to test positioning, 'q' to quit")
    
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    
    # Create hidden root window
    root = ctk.CTk()
    root.withdraw()
    
    dialog_manager = StatusDialogManager()
    
    def show_test_dialog():
        """Show a test dialog at cursor position"""
        print("📍 Showing dialog near cursor...")
        dialog_manager.show_recording()
        
        # Auto-hide after 3 seconds
        root.after(3000, lambda: dialog_manager.hide())
    
    # Command line interaction
    def check_input():
        """Check for keyboard input"""
        try:
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key == 'q':
                    root.quit()
                    return
                elif key == '\r' or key == '\n':  # Enter key
                    show_test_dialog()
        except ImportError:
            # Fallback for non-Windows systems
            pass
        
        # Schedule next check
        root.after(100, check_input)
    
    # Start input checking
    root.after(100, check_input)
    
    # Auto-show first dialog
    root.after(500, show_test_dialog)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        if dialog_manager:
            dialog_manager.hide()

if __name__ == "__main__":
    print("🧪 WindVoice Transparent Dialog Test Suite")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "position":
        test_positioning()
    else:
        test_transparent_dialogs()
        
        # Optional positioning test
        response = input("\n🎯 Do you want to test cursor positioning? (y/n): ")
        if response.lower().startswith('y'):
            test_positioning()
    
    print("\n✨ Test completed! Thank you for testing.")