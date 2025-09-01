import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from ..core.exceptions import AudioError


@dataclass
class AudioValidation:
    has_voice: bool
    rms_level: float
    duration: float
    file_size_mb: float


class AudioRecorder:
    def __init__(self, sample_rate: int = 44100, device: str = "default"):
        self.sample_rate = sample_rate
        self.device = device if device != "default" else None
        self.channels = 1  # Mono for voice
        self.recording = False
        self.audio_data: Optional[np.ndarray] = None
        self.temp_dir = Path(tempfile.gettempdir()) / "windvoice"
        self.temp_dir.mkdir(exist_ok=True)
        
    def get_available_devices(self) -> list:
        try:
            devices = sd.query_devices()
            input_devices = []
            for idx, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'index': idx,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })
            return input_devices
        except Exception as e:
            raise AudioError(f"Failed to query audio devices: {e}")
    
    def test_device(self, device_index: Optional[int] = None) -> bool:
        try:
            test_duration = 0.1  # 100ms test
            test_data = sd.rec(
                int(test_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index,
                dtype='float32'
            )
            sd.wait()
            return True
        except Exception:
            return False
    
    def start_recording(self):
        if self.recording:
            raise AudioError("Recording is already in progress")
            
        try:
            # Pre-allocate buffer for up to 30 seconds of audio
            max_duration = 30
            buffer_size = int(max_duration * self.sample_rate)
            
            self.audio_data = sd.rec(
                buffer_size,
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                dtype='float32'
            )
            self.recording = True
            
        except Exception as e:
            raise AudioError(f"Failed to start recording: {e}")
    
    def stop_recording(self) -> str:
        if not self.recording:
            raise AudioError("No recording in progress")
            
        try:
            sd.stop()
            sd.wait()
            self.recording = False
            
            if self.audio_data is None:
                raise AudioError("No audio data captured")
            
            # Trim silence from the end
            audio_trimmed = self._trim_silence(self.audio_data)
            
            # Save to temporary WAV file
            temp_file = self.temp_dir / f"recording_{asyncio.get_event_loop().time():.0f}.wav"
            sf.write(
                str(temp_file),
                audio_trimmed,
                self.sample_rate,
                subtype='PCM_16'
            )
            
            return str(temp_file)
            
        except Exception as e:
            self.recording = False
            raise AudioError(f"Failed to stop recording: {e}")
    
    def _trim_silence(self, audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        # Find the last non-silent sample
        rms_values = np.sqrt(np.mean(audio_data**2, axis=1) if len(audio_data.shape) > 1 else audio_data**2)
        
        # Find last index where RMS is above threshold
        last_sound_idx = len(rms_values) - 1
        for i in range(len(rms_values) - 1, -1, -1):
            if rms_values[i] > threshold:
                last_sound_idx = i
                break
        
        # Add small buffer after last sound (0.5 seconds)
        buffer_samples = int(0.5 * self.sample_rate)
        end_idx = min(len(audio_data), last_sound_idx + buffer_samples)
        
        return audio_data[:end_idx]
    
    def validate_audio_file(self, file_path: str, 
                          silence_threshold: float = 0.01,
                          min_duration: float = 0.5) -> AudioValidation:
        try:
            audio_data, sample_rate = sf.read(file_path)
            
            # Calculate RMS level
            if len(audio_data.shape) > 1:
                rms = np.sqrt(np.mean(audio_data**2))
            else:
                rms = np.sqrt(np.mean(audio_data**2))
            
            # Calculate duration
            duration = len(audio_data) / sample_rate
            
            # Calculate file size
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            
            # Determine if audio contains voice
            has_voice = rms > silence_threshold and duration >= min_duration
            
            return AudioValidation(
                has_voice=has_voice,
                rms_level=float(rms),
                duration=float(duration),
                file_size_mb=float(file_size_mb)
            )
            
        except Exception as e:
            raise AudioError(f"Failed to validate audio file: {e}")
    
    def cleanup_temp_files(self):
        try:
            for temp_file in self.temp_dir.glob("recording_*.wav"):
                if temp_file.exists():
                    temp_file.unlink()
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")
    
    def is_recording(self) -> bool:
        return self.recording
    
    async def record_with_timeout(self, max_duration: float = 30.0) -> str:
        self.start_recording()
        
        try:
            # Wait for either manual stop or timeout
            await asyncio.sleep(max_duration)
            
            if self.recording:
                return self.stop_recording()
            else:
                raise AudioError("Recording was stopped before timeout")
                
        except Exception as e:
            if self.recording:
                try:
                    sd.stop()
                    self.recording = False
                except:
                    pass
            raise e