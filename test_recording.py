#!/usr/bin/env python3
"""
Quick Recording Test Script

Test the audio recording and validation system independently.
"""

import sys
import asyncio
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_audio_devices():
    """Test audio device detection"""
    print("Testing audio devices...")
    
    try:
        from windvoice.services.audio import AudioRecorder
        
        recorder = AudioRecorder()
        devices = recorder.get_available_devices()
        
        print(f"Found {len(devices)} audio input devices:")
        for i, device in enumerate(devices):
            print(f"  {i}: {device['name']}")
            
        return len(devices) > 0
        
    except Exception as e:
        print(f"Error testing audio devices: {e}")
        return False


def test_audio_recording():
    """Test a quick audio recording"""
    print("\nTesting audio recording...")
    print("You have 3 seconds to speak after 'Recording...' appears")
    
    try:
        from windvoice.services.audio import AudioRecorder
        
        recorder = AudioRecorder()
        
        # Countdown
        for i in range(3, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)
        
        print("Recording... (speak now for 3 seconds)")
        
        # Start recording
        recorder.start_recording()
        time.sleep(3)  # Record for 3 seconds
        
        # Stop recording
        audio_file = recorder.stop_recording()
        print(f"Recording saved to: {audio_file}")
        
        return audio_file
        
    except Exception as e:
        print(f"Error during recording: {e}")
        return None


def test_audio_validation(audio_file):
    """Test audio validation"""
    if not audio_file:
        print("No audio file to validate")
        return
    
    print(f"\nValidating audio file: {Path(audio_file).name}")
    
    try:
        from windvoice.services.audio import AudioRecorder
        
        recorder = AudioRecorder()
        
        # Get detailed metrics
        metrics = recorder.get_quality_metrics(audio_file)
        title, message = recorder.get_validation_message(audio_file)
        
        print(f"\nValidation Results:")
        print(f"  Title: {title}")
        print(f"  Message: {message}")
        print(f"\nDetailed Metrics:")
        print(f"  Has voice: {metrics.has_voice}")
        print(f"  Duration: {metrics.duration:.2f} seconds")
        print(f"  RMS level: {metrics.rms_level:.6f}")
        print(f"  Peak level: {metrics.peak_level:.6f}")
        print(f"  Voice activity ratio: {metrics.voice_activity_ratio:.2%}")
        print(f"  Quality score: {metrics.quality_score:.0f}/100")
        print(f"  File size: {metrics.file_size_mb:.2f} MB")
        
        # Legacy validation for comparison
        legacy_validation = recorder.validate_audio_file(audio_file)
        print(f"\nLegacy Validation:")
        print(f"  Has voice: {legacy_validation.has_voice}")
        print(f"  RMS: {legacy_validation.rms_level:.6f}")
        
        return metrics.has_voice
        
    except Exception as e:
        print(f"Error validating audio: {e}")
        return False


def test_threshold_adjustment():
    """Test different threshold settings"""
    print("\nTesting threshold adjustment...")
    
    try:
        from windvoice.utils.audio_validation import AudioValidator
        
        validator = AudioValidator()
        
        print("Current thresholds:")
        print(f"  Silence threshold: {validator.silence_threshold_rms}")
        print(f"  Voice threshold: {validator.voice_threshold_rms}")
        print(f"  Min duration: {validator.min_duration} seconds")
        
        # Test with even more permissive settings
        print("\nTesting with extra-permissive settings...")
        custom_thresholds = {
            'silence_threshold_rms': 0.001,  # Very low
            'voice_threshold_rms': 0.005,    # Very low
            'min_duration': 0.1              # Very short
        }
        
        print("Extra-permissive thresholds:")
        for key, value in custom_thresholds.items():
            print(f"  {key}: {value}")
            
        return True
        
    except Exception as e:
        print(f"Error testing thresholds: {e}")
        return False


async def main():
    """Main test function"""
    print("WindVoice Recording Test")
    print("=" * 30)
    
    # Test 1: Audio devices
    if not test_audio_devices():
        print("❌ No audio devices found - cannot continue")
        return
    
    # Test 2: Threshold info
    test_threshold_adjustment()
    
    # Test 3: Record audio
    audio_file = test_audio_recording()
    
    if not audio_file:
        print("❌ Recording failed - cannot continue")
        return
    
    # Test 4: Validate audio
    has_voice = test_audio_validation(audio_file)
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    if has_voice:
        print("✅ Voice detected in recording!")
        print("The audio validation system is working correctly.")
    else:
        print("⚠️ No voice detected in recording")
        print("This could mean:")
        print("  1. You didn't speak during the recording")
        print("  2. Your microphone level is too low")
        print("  3. The thresholds need further adjustment")
    
    # Keep the audio file for inspection
    print(f"\nAudio file kept at: {audio_file}")
    print("You can inspect this file manually or through the settings panel.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")