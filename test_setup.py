#!/usr/bin/env python3
"""
WindVoice-Windows Setup Test Script

Tests all components to ensure they work correctly and helps diagnose issues.
"""

import sys
import asyncio
import tempfile
import time
from pathlib import Path
import numpy as np

# Add src to path for testing
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Core components
        from windvoice.core.config import ConfigManager
        from windvoice.core.app import WindVoiceApp
        from windvoice.services.audio import AudioRecorder
        from windvoice.services.transcription import TranscriptionService
        from windvoice.services.injection import TextInjectionService
        from windvoice.services.hotkeys import HotkeyManager
        from windvoice.ui.menubar import SystemTrayService
        from windvoice.ui.settings import SettingsWindow
        from windvoice.ui.popup import show_smart_popup
        from windvoice.utils.audio_validation import AudioValidator
        
        print("✅ All WindVoice modules imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_configuration():
    """Test configuration management"""
    print("\n🔧 Testing configuration...")
    
    try:
        from windvoice.core.config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print(f"✅ Configuration loaded")
        print(f"   Config file: {config_manager.config_file_path}")
        print(f"   Hotkey: {config.app.hotkey}")
        print(f"   Sample rate: {config.app.sample_rate}")
        print(f"   Theme: {config.ui.theme}")
        
        # Check if API is configured
        has_api = all([
            config.litellm.api_key,
            config.litellm.api_base,
            config.litellm.key_alias
        ])
        
        if has_api:
            print("✅ LiteLLM API is configured")
        else:
            print("⚠️ LiteLLM API not configured - run setup_config.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_audio_system():
    """Test audio recording system"""
    print("\n🎤 Testing audio system...")
    
    try:
        from windvoice.services.audio import AudioRecorder
        
        # Create audio recorder
        recorder = AudioRecorder()
        
        # Test device enumeration
        devices = recorder.get_available_devices()
        print(f"✅ Found {len(devices)} audio devices")
        
        for i, device in enumerate(devices[:3]):  # Show first 3
            print(f"   {i}: {device['name']} ({device['channels']} channels)")
        
        # Test device functionality
        if devices:
            test_device_id = devices[0]['index'] if devices else None
            can_record = recorder.test_device(test_device_id)
            
            if can_record:
                print("✅ Audio device test passed")
            else:
                print("⚠️ Audio device test failed - check microphone permissions")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        return False


def test_audio_validation():
    """Test audio validation system"""
    print("\n🔍 Testing audio validation...")
    
    try:
        from windvoice.utils.audio_validation import AudioValidator
        import soundfile as sf
        
        validator = AudioValidator()
        
        # Create a test audio file (1 second of sine wave)
        sample_rate = 44100
        duration = 1.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)  # Moderate volume
        
        # Save test file
        test_file = Path(tempfile.gettempdir()) / "windvoice_test.wav"
        sf.write(str(test_file), audio_data, sample_rate)
        
        # Validate the test file
        metrics = validator.validate_audio_file(str(test_file))
        
        print(f"✅ Audio validation successful")
        print(f"   Has voice: {metrics.has_voice}")
        print(f"   RMS level: {metrics.rms_level:.4f}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Quality score: {metrics.quality_score:.0f}/100")
        
        # Clean up
        test_file.unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Audio validation test failed: {e}")
        return False


def test_ui_components():
    """Test UI components (without actually showing them)"""
    print("\n🖥️ Testing UI components...")
    
    try:
        from windvoice.ui.settings import SettingsWindow
        from windvoice.ui.menubar import SystemTrayService
        from windvoice.core.config import ConfigManager
        import customtkinter as ctk
        
        # Test CustomTkinter availability
        print("✅ CustomTkinter available")
        
        # Test settings window creation (don't show it)
        config_manager = ConfigManager()
        settings_window = SettingsWindow(config_manager)
        print("✅ Settings window can be created")
        
        # Test system tray service creation
        tray_service = SystemTrayService()
        print("✅ System tray service can be created")
        
        return True
        
    except Exception as e:
        print(f"❌ UI components test failed: {e}")
        return False


def test_hotkey_system():
    """Test hotkey system (without actually registering hotkeys)"""
    print("\n⌨️ Testing hotkey system...")
    
    try:
        from windvoice.services.hotkeys import HotkeyManager
        
        hotkey_manager = HotkeyManager()
        
        # Test hotkey parsing
        test_hotkey = "ctrl+shift+space"
        hotkey_manager.set_hotkey(test_hotkey)
        print(f"✅ Hotkey system functional")
        print(f"   Test hotkey: {test_hotkey}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hotkey system test failed: {e}")
        return False


def test_text_injection():
    """Test text injection system"""
    print("\n💉 Testing text injection...")
    
    try:
        from windvoice.services.injection import TextInjectionService
        
        injection_service = TextInjectionService()
        print("✅ Text injection service can be created")
        
        # Note: We don't actually inject text during testing
        print("   (Actual injection not tested to avoid interfering with system)")
        
        return True
        
    except Exception as e:
        print(f"❌ Text injection test failed: {e}")
        return False


async def test_full_integration():
    """Test full application integration"""
    print("\n🔗 Testing full integration...")
    
    try:
        from windvoice.core.app import WindVoiceApp
        
        # Create app instance
        app = WindVoiceApp()
        print("✅ WindVoice app can be created")
        
        # Test initialization (without starting)
        try:
            await app.initialize()
            print("✅ App initialization successful")
            
            # Test cleanup
            await app.stop()
            print("✅ App cleanup successful")
            
        except Exception as init_error:
            if "LiteLLM configuration required" in str(init_error):
                print("⚠️ App initialization skipped - LiteLLM not configured")
                print("   Run setup_config.py to configure API credentials")
            else:
                raise init_error
        
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {e}")
        return False


def print_system_info():
    """Print system information"""
    print("💻 System Information")
    print("=" * 30)
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {Path.cwd()}")
    
    # Check temp directory
    temp_dir = Path(tempfile.gettempdir()) / "windvoice"
    print(f"Temp directory: {temp_dir}")
    print(f"Temp dir exists: {temp_dir.exists()}")
    
    print()


async def run_all_tests():
    """Run all tests"""
    print_system_info()
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Audio System Test", test_audio_system),
        ("Audio Validation Test", test_audio_validation),
        ("UI Components Test", test_ui_components),
        ("Hotkey System Test", test_hotkey_system),
        ("Text Injection Test", test_text_injection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Full integration test (async)
    try:
        integration_result = await test_full_integration()
        results.append(("Full Integration Test", integration_result))
    except Exception as e:
        print(f"❌ Full Integration Test crashed: {e}")
        results.append(("Full Integration Test", False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}")
            passed += 1
        else:
            print(f"❌ {test_name}")
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nWindVoice setup appears to be working correctly.")
        print("\nNext steps:")
        print("1. Configure LiteLLM API: python setup_config.py")
        print("2. Run WindVoice: python main.py")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED")
        print("\nPlease review the errors above and:")
        print("1. Install missing dependencies: python install_dependencies.py")
        print("2. Check your system permissions (especially microphone access)")
        print("3. Ensure you're running on Windows with Python 3.8+")
    
    return failed == 0


def main():
    """Main test runner"""
    print("🧪 WindVoice-Windows Setup Test")
    print("=" * 50)
    
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()