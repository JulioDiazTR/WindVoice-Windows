import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from ..core.exceptions import AudioError
from ..utils.audio_validation import AudioValidator, AudioQualityMetrics
from ..utils.logging import get_logger, WindVoiceLogger


@dataclass
class AudioValidation:
    has_voice: bool
    rms_level: float
    duration: float
    file_size_mb: float
    
    @classmethod
    def from_quality_metrics(cls, metrics: AudioQualityMetrics) -> 'AudioValidation':
        """Create AudioValidation from AudioQualityMetrics for backward compatibility"""
        return cls(
            has_voice=metrics.has_voice,
            rms_level=metrics.rms_level,
            duration=metrics.duration,
            file_size_mb=metrics.file_size_mb
        )


class AudioRecorder:
    def __init__(self, sample_rate: int = 44100, device: str = "default"):
        self.logger = get_logger("audio")
        
        self.sample_rate = sample_rate
        self.device = device if device != "default" else None
        self.channels = 1  # Mono for voice
        self.recording = False
        self.audio_data: Optional[np.ndarray] = None
        self.temp_dir = Path(tempfile.gettempdir()) / "windvoice"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Advanced audio validator
        self.audio_validator = AudioValidator()
        
        # Recording state tracking
        self.recording_start_time: Optional[float] = None
        self.recording_levels: list = []  # For real-time level monitoring
        
        # Log initialization
        WindVoiceLogger.log_audio_workflow_step(
            self.logger, 
            "AudioRecorder_Initialized", 
            {
                "sample_rate": sample_rate,
                "device": device,
                "channels": self.channels,
                "temp_dir": str(self.temp_dir)
            }
        )
        
    def get_available_devices(self) -> list:
        try:
            self.logger.debug("Querying available audio devices...")
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
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Available_Devices_Found",
                {"device_count": len(input_devices)}
            )
            for device in input_devices:
                self.logger.debug(f"   Device {device['index']}: {device['name']} ({device['channels']} channels, {device['sample_rate']} Hz)")
            
            return input_devices
        except Exception as e:
            self.logger.error(f"Failed to query audio devices: {e}")
            raise AudioError(f"Failed to query audio devices: {e}")
    
    def test_device(self, device_index: Optional[int] = None) -> bool:
        self.logger.info(f"Testing microphone device (index: {device_index})")
        try:
            test_duration = 0.1  # 100ms test
            self.logger.debug(f"Starting {test_duration}s test recording...")
            
            test_data = sd.rec(
                int(test_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index,
                dtype='float32'
            )
            sd.wait()
            
            # Analyze test data
            import numpy as np
            max_amplitude = np.max(np.abs(test_data))
            rms = np.sqrt(np.mean(test_data**2))
            
            self.logger.info(f"✅ Microphone test successful - max_amplitude: {max_amplitude:.6f}, rms: {rms:.6f}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Microphone test failed: {e}")
            return False
    
    def start_recording(self):
        WindVoiceLogger.log_audio_workflow_step(
            self.logger,
            "start_recording_CALLED",
            {"currently_recording": self.recording}
        )
        
        if self.recording:
            self.logger.error("Recording is already in progress - cannot start new recording")
            raise AudioError("Recording is already in progress")
            
        try:
            # Pre-allocate buffer for up to 30 seconds of audio
            max_duration = 30
            buffer_size = int(max_duration * self.sample_rate)
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Buffer_Setup",
                {
                    "max_duration_sec": max_duration,
                    "buffer_size_samples": buffer_size,
                    "device": self.device,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels
                }
            )
            
            # Test device first
            self.logger.debug(f"Testing audio device before recording...")
            if not self.test_device(self.device):
                raise AudioError(f"Audio device test failed for device: {self.device}")
            
            # CRITICAL FIX: Clear any previous audio data to prevent caching bug
            self.audio_data = None
            
            self.logger.info(f"Starting sounddevice recording...")
            self.audio_data = sd.rec(
                buffer_size,
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                dtype='float32'
            )
            
            self.recording = True
            self.recording_start_time = asyncio.get_event_loop().time()
            self.recording_levels.clear()
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Started_SUCCESS",
                {
                    "start_time": self.recording_start_time,
                    "buffer_shape": str(self.audio_data.shape) if self.audio_data is not None else "None"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.recording = False
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Start_FAILED",
                {"error": str(e)}
            )
            raise AudioError(f"Failed to start recording: {e}")
    
    def get_current_level(self) -> float:
        """Get current recording level for real-time feedback"""
        if not self.recording or self.audio_data is None:
            return 0.0
            
        try:
            # Get current position in recording
            current_samples = sd.default.current_frame
            if current_samples > 0 and current_samples < len(self.audio_data):
                # Calculate RMS of recent samples (last 100ms)
                recent_samples = int(0.1 * self.sample_rate)
                start_idx = max(0, current_samples - recent_samples)
                recent_audio = self.audio_data[start_idx:current_samples]
                
                if len(recent_audio) > 0:
                    level = float(np.sqrt(np.mean(recent_audio**2)))
                    self.recording_levels.append(level)
                    return level
                    
            return 0.0
            
        except Exception:
            return 0.0
    
    def stop_recording(self) -> str:
        WindVoiceLogger.log_audio_workflow_step(
            self.logger,
            "stop_recording_CALLED",
            {"currently_recording": self.recording}
        )
        
        if not self.recording:
            self.logger.error("No recording in progress - cannot stop recording")
            raise AudioError("No recording in progress")
            
        try:
            self.logger.info("Stopping sounddevice recording...")
            sd.stop()
            sd.wait()
            
            recording_duration = None
            if self.recording_start_time:
                recording_duration = asyncio.get_event_loop().time() - self.recording_start_time
            
            self.recording = False
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Stopped",
                {
                    "duration_sec": recording_duration,
                    "audio_data_exists": self.audio_data is not None,
                    "audio_data_shape": str(self.audio_data.shape) if self.audio_data is not None else "None"
                }
            )
            
            if self.audio_data is None:
                self.logger.error("No audio data captured despite recording")
                raise AudioError("No audio data captured")
            
            # Log raw audio statistics before trimming
            raw_duration = len(self.audio_data) / self.sample_rate
            raw_rms = float(np.sqrt(np.mean(self.audio_data**2)))
            raw_max_amplitude = float(np.max(np.abs(self.audio_data)))
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Raw_Audio_Analysis",
                {
                    "raw_duration_sec": raw_duration,
                    "raw_rms_level": raw_rms,
                    "raw_max_amplitude": raw_max_amplitude,
                    "raw_samples": len(self.audio_data)
                }
            )
            
            # Trim silence from the end
            self.logger.debug("Trimming silence from audio...")
            audio_trimmed = self._trim_silence(self.audio_data)
            
            trimmed_duration = len(audio_trimmed) / self.sample_rate
            trimmed_rms = float(np.sqrt(np.mean(audio_trimmed**2)))
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_Trimmed",
                {
                    "trimmed_duration_sec": trimmed_duration,
                    "trimmed_rms_level": trimmed_rms,
                    "trimmed_samples": len(audio_trimmed),
                    "reduction_ratio": len(audio_trimmed) / len(self.audio_data) if len(self.audio_data) > 0 else 0
                }
            )
            
            # Save to temporary WAV file
            temp_file = self.temp_dir / f"recording_{asyncio.get_event_loop().time():.0f}.wav"
            self.logger.debug(f"Saving audio to: {temp_file}")
            
            sf.write(
                str(temp_file),
                audio_trimmed,
                self.sample_rate,
                subtype='PCM_16'
            )
            
            file_size_mb = temp_file.stat().st_size / (1024 * 1024)
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_File_Saved",
                {
                    "file_path": str(temp_file),
                    "file_size_mb": file_size_mb,
                    "file_exists": temp_file.exists()
                }
            )
            
            # CRITICAL FIX: Clear audio data after saving to prevent buffer reuse
            self.audio_data = None
            
            return str(temp_file)
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            self.recording = False
            # Clear audio data on error too
            self.audio_data = None
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Stop_FAILED",
                {"error": str(e)}
            )
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
                          silence_threshold: float = 0.005,
                          min_duration: float = 0.3) -> AudioValidation:
        """Validate audio file using advanced audio validator"""
        WindVoiceLogger.log_audio_workflow_step(
            self.logger,
            "validate_audio_file_CALLED",
            {"file_path": file_path, "file_exists": Path(file_path).exists()}
        )
        
        try:
            # Use the advanced validator
            quality_metrics = self.audio_validator.validate_audio_file(file_path)
            
            # Log detailed validation results
            WindVoiceLogger.log_validation_result(
                self.logger,
                "Audio_File_Validation",
                {
                    "has_voice": quality_metrics.has_voice,
                    "rms_level": quality_metrics.rms_level,
                    "duration_sec": quality_metrics.duration,
                    "file_size_mb": quality_metrics.file_size_mb,
                    "quality_score": quality_metrics.quality_score,
                    "noise_level": quality_metrics.noise_level,
                    "voice_activity_ratio": quality_metrics.voice_activity_ratio
                }
            )
            
            # Convert to legacy AudioValidation format for backward compatibility
            result = AudioValidation.from_quality_metrics(quality_metrics)
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_Validation_Complete",
                {"validation_passed": result.has_voice}
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate audio file: {e}")
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_Validation_FAILED",
                {"error": str(e)}
            )
            raise AudioError(f"Failed to validate audio file: {e}")
    
    def get_quality_metrics(self, file_path: str) -> AudioQualityMetrics:
        """Get detailed audio quality metrics"""
        try:
            return self.audio_validator.validate_audio_file(file_path)
        except Exception as e:
            raise AudioError(f"Failed to get audio quality metrics: {e}")
    
    def get_validation_message(self, file_path: str) -> Tuple[str, str]:
        """Get user-friendly validation message"""
        try:
            metrics = self.get_quality_metrics(file_path)
            return self.audio_validator.get_validation_message(metrics)
        except Exception as e:
            return "Validation Error", f"Failed to validate audio: {e}"
    
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