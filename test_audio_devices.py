#!/usr/bin/env python3
"""
Test script to diagnose audio device issues with WindVoice
"""

import sys
sys.path.insert(0, 'src')

from windvoice.services.audio import AudioRecorder
from windvoice.utils.logging import setup_logging
import asyncio
import time

async def test_audio_devices():
    """Test all available audio devices and their functionality"""
    
    logger = setup_logging("DEBUG", False)  # Console only
    
    print("=== WindVoice Audio Device Diagnostic ===\n")
    
    # Create audio recorder
    recorder = AudioRecorder()
    
    # List all available devices
    print("📱 Available Audio Input Devices:")
    print("-" * 50)
    devices = recorder.get_available_devices()
    
    for i, device in enumerate(devices):
        print(f"{i+1:2d}. {device['name']}")
        print(f"     Index: {device['index']}")
        print(f"     Channels: {device['channels']}")
        print(f"     Sample Rate: {device['sample_rate']} Hz")
        
        # Test device
        test_result = recorder.test_device(device['index'])
        status = "✅ WORKING" if test_result else "❌ FAILED"
        print(f"     Status: {status}")
        print()
    
    # Find working devices
    working_devices = [d for d in devices if recorder.test_device(d['index'])]
    
    if not working_devices:
        print("❌ No working audio devices found!")
        return
        
    print(f"\n🎤 Testing Recording with Working Devices ({len(working_devices)} found):")
    print("-" * 60)
    
    # Test each working device
    for device in working_devices[:3]:  # Test first 3 working devices
        await test_recording_with_device(recorder, device)
        
async def test_recording_with_device(recorder: AudioRecorder, device: dict):
    """Test recording with a specific device"""
    print(f"\n📱 Testing Device: {device['name']} (Index: {device['index']})")
    print("-" * 50)
    
    try:
        # Create a new recorder with this specific device
        device_recorder = AudioRecorder(device=device['index'])
        
        print("Starting 3-second test recording...")
        print("Please speak clearly now!")
        
        device_recorder.start_recording()
        
        # Monitor levels during recording
        for i in range(30):  # 3 seconds
            level = device_recorder.get_current_level()
            bar = "█" * int(level * 50) if level > 0 else "▯"
            print(f"\rLevel: [{bar:<20}] {level:.4f}", end="", flush=True)
            await asyncio.sleep(0.1)
        
        print("\nStopping recording...")
        audio_file = device_recorder.stop_recording()
        
        print(f"✅ Audio saved to: {audio_file}")
        
        # Analyze the audio
        print("\n📊 Audio Analysis:")
        print("-" * 30)
        
        validation = device_recorder.validate_audio_file(audio_file)
        quality_metrics = device_recorder.get_quality_metrics(audio_file)
        title, message = device_recorder.get_validation_message(audio_file)
        
        print(f"Duration: {validation.duration:.2f} seconds")
        print(f"RMS Level: {validation.rms_level:.6f}")
        print(f"File Size: {validation.file_size_mb:.2f} MB")
        print(f"Voice Detected: {'✅ YES' if validation.has_voice else '❌ NO'}")
        print(f"Quality Score: {quality_metrics.quality_score:.1f}/100")
        print(f"Voice Activity: {quality_metrics.voice_activity_ratio:.3f}")
        print(f"Noise Level: {quality_metrics.noise_level:.6f}")
        
        print(f"\n💬 User Message: {title}")
        print(f"   {message}")
        
        if not validation.has_voice:
            print("\n⚠️  NO VOICE DETECTED with this device")
        else:
            print(f"\n✅ SUCCESS: Voice detected with {device['name']}")
            return True
            
    except Exception as e:
        print(f"\n❌ Recording test failed: {e}")
        return False
    
    return False

if __name__ == "__main__":
    asyncio.run(test_audio_devices())