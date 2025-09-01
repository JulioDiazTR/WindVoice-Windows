#!/usr/bin/env python3
"""
Simple Windows microphone test using built-in Windows audio APIs
"""

import sounddevice as sd
import numpy as np
import time

def test_windows_microphone():
    """Test Windows microphone directly with sounddevice"""
    
    print("=== Windows Microphone Test ===\n")
    
    try:
        # List all input devices
        devices = sd.query_devices()
        input_devices = [(i, d) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        
        print("Available input devices:")
        for i, (idx, device) in enumerate(input_devices):
            print(f"{i+1}. {device['name']} (Index {idx})")
        
        if not input_devices:
            print("❌ No input devices found!")
            return
        
        # Test default input device
        print(f"\n🎤 Testing default input device...")
        print("Speak now for 5 seconds...")
        
        # Record 5 seconds of audio
        duration = 5  # seconds  
        sample_rate = 44100
        
        print("Recording...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, 
                           channels=1, dtype='float32')
        sd.wait()  # Wait until recording is finished
        
        # Analyze the captured audio
        audio_flat = audio_data.flatten()
        rms = np.sqrt(np.mean(audio_flat**2))
        max_amplitude = np.max(np.abs(audio_flat))
        
        print(f"\n📊 Results:")
        print(f"Duration: {duration} seconds")
        print(f"Samples: {len(audio_flat)}")
        print(f"RMS Level: {rms:.6f}")
        print(f"Max Amplitude: {max_amplitude:.6f}")
        
        if rms > 0.001:  # Threshold for detecting sound
            print("✅ SUCCESS: Microphone is working and capturing audio!")
            print(f"   Signal strength: {'Strong' if rms > 0.01 else 'Weak' if rms > 0.005 else 'Very weak'}")
        else:
            print("❌ PROBLEM: No significant audio detected")
            print("\n🔧 Troubleshooting steps:")
            print("1. Check if microphone is muted in Windows sound settings")
            print("2. Verify microphone privacy settings (Windows 10/11)")
            print("3. Try speaking louder or closer to the microphone")
            print("4. Check if another application is using the microphone")
            print("5. Test microphone with Windows Voice Recorder app")
        
        # Show a simple volume meter for real-time feedback
        print(f"\n🎚️ Real-time microphone test (speak now for 10 seconds):")
        print("Press Ctrl+C to stop")
        
        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32') as stream:
                for _ in range(100):  # 10 seconds at 0.1s intervals
                    audio_chunk, _ = stream.read(int(sample_rate * 0.1))
                    chunk_rms = np.sqrt(np.mean(audio_chunk**2))
                    
                    # Create visual level meter
                    level_bars = int(chunk_rms * 50)
                    meter = "█" * level_bars + "▯" * (20 - level_bars)
                    print(f"\rLevel: [{meter}] {chunk_rms:.4f}", end="", flush=True)
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nTest stopped by user")
        
        print(f"\n\n{'='*50}")
        print("Test complete!")
        
    except Exception as e:
        print(f"❌ Error during microphone test: {e}")

if __name__ == "__main__":
    test_windows_microphone()