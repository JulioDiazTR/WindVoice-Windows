#!/usr/bin/env python3
"""
WindVoice-Windows Launch Script

Safe launcher for WindVoice with proper error handling and user guidance.
"""

import sys
import asyncio
import signal
import os
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))


def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'customtkinter',
        'sounddevice', 
        'soundfile',
        'numpy',
        'pynput',
        'pystray',
        'aiohttp'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Missing required dependencies:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\nTo install dependencies, run:")
        print("   python install_dependencies.py")
        return False
    
    return True


def setup_signal_handlers(app):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\n📡 Received signal {signum}, shutting down gracefully...")
        if app and hasattr(app, 'running'):
            app.running = False
        sys.exit(0)
    
    if sys.platform == "win32":
        import signal
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def run_windvoice():
    """Run WindVoice with proper error handling"""
    print("Starting WindVoice-Windows...")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        return False
    
    try:
        # Import after dependency check
        from windvoice.core.app import WindVoiceApp
        
        # Create app instance
        app = WindVoiceApp()
        
        # Setup signal handlers
        setup_signal_handlers(app)
        
        # Initialize and start
        await app.initialize()
        print("\nWindVoice initialized successfully!")
        print(f"System tray icon should be visible (look for blue icon)")
        print(f"Press {app.config.app.hotkey} to start recording")
        print("Press Ctrl+C to stop WindVoice")
        print("\n" + "=" * 40)
        
        await app.start()
        
        return True
        
    except KeyboardInterrupt:
        print("\n\nWindVoice stopped by user (Ctrl+C)")
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        if "LiteLLM configuration required" in error_msg:
            print("\nConfiguration needed!")
            print("=" * 30)
            print("WindVoice needs to be configured with your LiteLLM API credentials.")
            print("\nTo configure WindVoice:")
            print("   python setup_config.py")
            print("\nOr manually edit the config file with your API credentials.")
            return False
            
        elif "No default root window" in error_msg:
            print("\nUI Error!")
            print("=" * 20)  
            print("There was an issue initializing the UI system.")
            print("This is usually a temporary issue. Please try:")
            print("1. Close any other Python/Tkinter applications")
            print("2. Run WindVoice again")
            return False
            
        elif "audio" in error_msg.lower() or "microphone" in error_msg.lower():
            print("\nAudio System Error!")
            print("=" * 25)
            print("There was an issue with the audio system:")
            print(f"   {error_msg}")
            print("\nTo fix this:")
            print("1. Check that your microphone is connected")
            print("2. Check microphone permissions for Python")
            print("3. Try running: python test_setup.py")
            return False
            
        else:
            print(f"\nUnexpected error: {e}")
            print("\nFor help:")
            print("1. Run diagnostics: python test_setup.py")
            print("2. Check the GitHub issues page")
            return False


def show_startup_info():
    """Show startup information"""
    print("WindVoice-Windows")
    print("=" * 20)
    print("Native Windows voice dictation with AI transcription")
    print("Created for Thomson Reuters LiteLLM integration")
    print()


def main():
    """Main entry point"""
    show_startup_info()
    
    try:
        success = asyncio.run(run_windvoice())
        if success:
            print("\nWindVoice ended successfully")
        else:
            print("\nWindVoice ended with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nStartup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nCritical startup error: {e}")
        print("\nPlease check your installation and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()