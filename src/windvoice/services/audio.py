import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from ..core.exceptions import AudioError, AudioDeviceBusyError
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
    def __init__(self, sample_rate: int = 16000, device: str = "default"):
        self.logger = get_logger("audio")
        
        # PERFORMANCE OPTIMIZATION: Default to 16kHz for Whisper optimization
        # 16kHz is Whisper's native sample rate, eliminates downsampling overhead
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
            seen_device_names = set()
            
            for idx, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    device_name = device['name'].strip()
                    
                    # Skip duplicates based on device name
                    if device_name not in seen_device_names:
                        seen_device_names.add(device_name)
                        input_devices.append({
                            'index': idx,
                            'name': device_name,
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
    
    def get_default_input_device(self) -> Optional[dict]:
        """Get the system's default input device information"""
        try:
            default_device = sd.query_devices(kind='input')
            if default_device and default_device['max_input_channels'] > 0:
                return {
                    'index': default_device['index'] if 'index' in default_device else None,
                    'name': default_device['name'].strip(),
                    'channels': default_device['max_input_channels'],
                    'sample_rate': default_device['default_samplerate']
                }
            return None
        except Exception as e:
            self.logger.error(f"Failed to get default input device: {e}")
            return None
    
    def _extract_device_index(self, device_name: str) -> Optional[int]:
        """Extract device index from device name string"""
        if not device_name or device_name == "default":
            return None
        
        # Extract index from format like "Device Name (ID: 123)"
        if "(ID: " in device_name and ")" in device_name:
            try:
                start = device_name.find("(ID: ") + 5
                end = device_name.find(")", start)
                index_str = device_name[start:end]
                return int(index_str)
            except (ValueError, IndexError):
                pass
        
        return None
    
    def is_device_available_for_exclusive_use(self, device_index: Optional[int] = None) -> Tuple[bool, str]:
        """Check if device is available for exclusive use (not busy with other apps)"""
        self.logger.info(f"Checking if device is available for exclusive use (index: {device_index})")
        
        try:
            # Try to open the device in exclusive mode first
            import sounddevice as sd
            
            # Test with a very short recording to see if device is truly available
            test_duration = 0.05  # 50ms test - very short to minimize disruption
            
            # Try to record with exclusive access
            test_data = sd.rec(
                int(test_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index,
                dtype='float32'
            )
            sd.wait()
            
            # If we got here, device is available
            self.logger.info("✅ Device is available for exclusive use")
            return True, "available"
            
        except Exception as e:
            error_msg = str(e).lower()
            self.logger.warning(f"⚠️  Device availability check failed: {e}")
            
            # Check for specific busy/in-use indicators
            if any(indicator in error_msg for indicator in [
                "device unavailable", "device busy", "access denied", 
                "another application", "already in use", "sharing violation",
                "resource busy", "device in use"
            ]):
                return False, "device_busy"
            elif any(indicator in error_msg for indicator in [
                "invalid device", "no input device", "no matching device", "paerrorcode -9996"
            ]):
                return False, "device_not_found"
            else:
                # Assume device is busy if we can't access it for unknown reasons
                return False, "device_busy"
    
    def test_device(self, device_index: Optional[int] = None) -> Tuple[bool, str]:
        """Test audio device and return success status with error reason"""
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
            return True, "success"
        except Exception as e:
            error_msg = str(e).lower()
            self.logger.error(f"❌ Microphone test failed: {e}")
            
            # Detect specific error types
            if "device unavailable" in error_msg or "device busy" in error_msg or "access denied" in error_msg:
                return False, "device_busy"
            elif "no input device matching" in error_msg and self.device and "(" in str(self.device) and "ID:" in str(self.device):
                # This error often occurs when device is busy/in use by another app (Teams, Zoom, etc.)
                return False, "device_busy"
            elif "no matching device" in error_msg:
                return False, "device_busy"  # Often indicates device is in use
            elif "paerrorcode -9992" in error_msg or "stream callback" in error_msg:
                return False, "device_busy"  # Device is in use by another application
            elif ("invalid device" in error_msg and "paerrorcode -9996" in error_msg):
                return False, "device_not_found"
            else:
                return False, "unknown_error"
    
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
            # PERFORMANCE OPTIMIZATION: Dynamic buffer allocation based on typical usage
            # Most voice recordings are <30 seconds, so start with reasonable buffer
            typical_duration = 30  # Optimized for typical voice recordings
            self.max_duration = 120  # Maximum supported duration
            self.buffer_size = int(typical_duration * self.sample_rate)
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Buffer_Setup",
                {
                    "optimized_duration_sec": typical_duration,
                    "max_duration_sec": self.max_duration,
                    "optimized_buffer_size_samples": self.buffer_size,
                    "device": self.device,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels
                }
            )
            
            # Check if device is available for exclusive use BEFORE attempting recording
            self.logger.debug(f"Checking device availability before recording...")
            device_index = self._extract_device_index(self.device) if isinstance(self.device, str) else self.device
            
            is_available, availability_reason = self.is_device_available_for_exclusive_use(device_index)
            if not is_available:
                if availability_reason == "device_busy":
                    self.logger.error(f"🔒 Device is busy/in use by another application: {self.device}")
                    raise AudioDeviceBusyError(f"Audio device is busy or in use by another application: {self.device}")
                else:
                    self.logger.error(f"❌ Device not available: {availability_reason}")
                    raise AudioError(f"Audio device not available: {self.device} ({availability_reason})")
            
            self.logger.info(f"✅ Device is available for recording: {self.device}")
            
            # CRITICAL FIX: Clear any previous audio data to prevent caching bug
            self.audio_data = None
            
            self.logger.info(f"Starting optimized sounddevice recording...")
            # PERFORMANCE: Use optimized buffer size instead of max duration
            self.audio_data = sd.rec(
                self.buffer_size,
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index,
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
                    "optimized_buffer_samples": self.buffer_size,
                    "optimized_buffer_duration": typical_duration
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
        """Get current recording level for real-time feedback - optimized"""
        if not self.recording or self.audio_data is None:
            return 0.0
            
        try:
            # Fast current level detection
            current_samples = min(sd.default.current_frame, len(self.audio_data))
            if current_samples > 100:  # Need at least 100 samples
                # Use smaller window for faster calculation (50ms instead of 100ms)
                recent_samples = int(0.05 * self.sample_rate)
                start_idx = max(0, current_samples - recent_samples)
                recent_audio = self.audio_data[start_idx:current_samples]
                
                if len(recent_audio) > 0:
                    # Fast RMS calculation
                    level = float(np.sqrt(np.mean(recent_audio**2)))
                    # Limit recording levels history to prevent memory growth
                    if len(self.recording_levels) > 100:
                        self.recording_levels = self.recording_levels[-50:]
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
            
            if self.audio_data is None:
                self.logger.error("No audio data captured despite recording")
                raise AudioError("No audio data captured")
            
            # PERFORMANCE OPTIMIZATION: Calculate actual samples recorded based on duration
            if recording_duration:
                actual_samples = min(
                    int(recording_duration * self.sample_rate),
                    len(self.audio_data)
                )
            else:
                # Fallback: use the current frame from sounddevice
                actual_samples = min(sd.default.current_frame, len(self.audio_data))
            
            # Only process the actual recorded portion (not the full 120s buffer)
            actual_audio_data = self.audio_data[:actual_samples] if actual_samples > 0 else self.audio_data
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Stopped",
                {
                    "duration_sec": recording_duration,
                    "total_buffer_samples": len(self.audio_data),
                    "actual_samples_used": actual_samples,
                    "efficiency_ratio": actual_samples / len(self.audio_data) if len(self.audio_data) > 0 else 0
                }
            )
            
            # Log actual audio statistics (not full buffer)
            actual_duration = len(actual_audio_data) / self.sample_rate
            actual_rms = float(np.sqrt(np.mean(actual_audio_data**2))) if len(actual_audio_data) > 0 else 0.0
            actual_max_amplitude = float(np.max(np.abs(actual_audio_data))) if len(actual_audio_data) > 0 else 0.0
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Actual_Audio_Analysis",
                {
                    "actual_duration_sec": actual_duration,
                    "actual_rms_level": actual_rms,
                    "actual_max_amplitude": actual_max_amplitude,
                    "actual_samples": len(actual_audio_data)
                }
            )
            
            # Fast trim silence from the end of actual data only
            self.logger.debug("Fast trimming silence from actual audio...")
            audio_trimmed = self._fast_trim_silence(actual_audio_data)
            
            trimmed_duration = len(audio_trimmed) / self.sample_rate
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_Trimmed",
                {
                    "trimmed_duration_sec": trimmed_duration,
                    "trimmed_samples": len(audio_trimmed),
                    "trim_reduction_ratio": len(audio_trimmed) / len(actual_audio_data) if len(actual_audio_data) > 0 else 0
                }
            )
            
            # Save audio file (already optimized at 16kHz for Whisper)
            temp_file = self.temp_dir / f"recording_{asyncio.get_event_loop().time():.0f}.wav"
            self.logger.debug(f"Saving Whisper-optimized audio to: {temp_file}")
            
            # PERFORMANCE: No downsampling needed - already recording at optimal 16kHz
            audio_optimized = audio_trimmed
            optimized_sample_rate = self.sample_rate
            
            self.logger.debug(f"Using native sample rate: {optimized_sample_rate}Hz (Whisper-optimized)")
            
            sf.write(
                str(temp_file),
                audio_optimized,
                optimized_sample_rate,
                subtype='PCM_16'
            )
            
            file_size_mb = temp_file.stat().st_size / (1024 * 1024)
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Optimized_Audio_File_Saved",
                {
                    "file_path": str(temp_file),
                    "file_size_mb": file_size_mb,
                    "optimized_sample_rate": optimized_sample_rate,
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
    
    def _fast_trim_silence(self, audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Fast silence trimming optimized for speed"""
        if len(audio_data) == 0:
            return audio_data
            
        # Use vectorized operations for speed
        # Calculate RMS in chunks for efficiency
        chunk_size = int(0.1 * self.sample_rate)  # 100ms chunks
        if chunk_size == 0:
            chunk_size = 1
            
        # Find last significant audio chunk
        last_sound_idx = 0
        for i in range(len(audio_data) - chunk_size, -1, -chunk_size):
            chunk_end = min(i + chunk_size, len(audio_data))
            chunk = audio_data[i:chunk_end]
            if len(chunk) > 0:
                chunk_rms = np.sqrt(np.mean(chunk**2))
                if chunk_rms > threshold:
                    last_sound_idx = chunk_end
                    break
        
        # Add small buffer (0.2 seconds instead of 0.5 for speed)
        buffer_samples = int(0.2 * self.sample_rate)
        end_idx = min(len(audio_data), last_sound_idx + buffer_samples)
        
        return audio_data[:end_idx]
    
    def _trim_silence(self, audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Legacy method - kept for backward compatibility"""
        return self._fast_trim_silence(audio_data, threshold)
    
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
    
    async def record_with_timeout(self, max_duration: float = 120.0) -> str:
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