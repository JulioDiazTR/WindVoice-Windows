"""
Advanced Audio Validation Utilities

Enhanced audio quality detection, silence analysis, and voice activity detection
for optimal transcription results.
"""

import numpy as np
import soundfile as sf
import scipy.signal
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional
import logging

from ..core.exceptions import AudioError


@dataclass
class AudioQualityMetrics:
    """Comprehensive audio quality metrics"""
    has_voice: bool
    rms_level: float
    peak_level: float
    duration: float
    file_size_mb: float
    sample_rate: int
    channels: int
    voice_activity_ratio: float
    noise_level: float
    dynamic_range: float
    clipping_detected: bool
    quality_score: float  # 0-100 scale


@dataclass
class VoiceActivitySegment:
    """Voice activity segment information"""
    start_time: float
    end_time: float
    duration: float
    confidence: float


class AudioValidator:
    """Advanced audio validation with voice activity detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Optimized thresholds for better voice detection (more permissive)
        self.silence_threshold_rms = 0.003 # RMS threshold for silence detection (further reduced for quiet voices)
        self.voice_threshold_rms = 0.005   # RMS threshold for voice detection (more sensitive)
        self.min_duration = 0.2            # Minimum recording duration (allow shorter valid recordings)
        self.max_duration = 120.0          # Maximum recording duration (2 minutes)
        self.clipping_threshold = 0.98     # Peak level for clipping detection
        self.noise_floor_percentile = 20   # Percentile for noise floor estimation (adaptive)
        
    def validate_audio_file(self, file_path: str) -> AudioQualityMetrics:
        """Comprehensive audio file validation"""
        try:
            # Load audio file
            audio_data, sample_rate = sf.read(file_path)
            
            # Ensure mono audio for analysis
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
                
            return self._analyze_audio(audio_data, sample_rate, file_path)
            
        except Exception as e:
            raise AudioError(f"Failed to validate audio file {file_path}: {e}")
            
    def validate_audio_data(self, audio_data: np.ndarray, sample_rate: int) -> AudioQualityMetrics:
        """Validate audio data directly"""
        try:
            # Ensure mono audio for analysis
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
                
            return self._analyze_audio(audio_data, sample_rate)
            
        except Exception as e:
            raise AudioError(f"Failed to validate audio data: {e}")
            
    def _analyze_audio(self, audio_data: np.ndarray, sample_rate: int, 
                      file_path: Optional[str] = None) -> AudioQualityMetrics:
        """Perform comprehensive audio analysis"""
        
        # Basic metrics
        duration = len(audio_data) / sample_rate
        rms_level = float(np.sqrt(np.mean(audio_data**2)))
        peak_level = float(np.max(np.abs(audio_data)))
        
        # File size (if available)
        file_size_mb = 0.0
        if file_path and Path(file_path).exists():
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        else:
            # Estimate size from audio data
            file_size_mb = (len(audio_data) * 2) / (1024 * 1024)  # 16-bit audio estimate
            
        # Voice activity detection
        voice_segments = self._detect_voice_activity(audio_data, sample_rate)
        voice_activity_ratio = self._calculate_voice_ratio(voice_segments, duration)
        
        # Noise analysis
        noise_level = self._estimate_noise_level(audio_data)
        
        # Dynamic range
        dynamic_range = self._calculate_dynamic_range(audio_data)
        
        # Clipping detection
        clipping_detected = peak_level > self.clipping_threshold
        
        # Voice detection logic (optimized for better sensitivity)
        has_voice = (
            duration >= self.min_duration and
            rms_level > self.voice_threshold_rms and
            voice_activity_ratio > 0.03 and  # At least 3% voice activity (more sensitive)
            not (noise_level > rms_level * 0.8)  # Not mostly noise (allow more background noise)
        )
        
        # Quality score calculation
        quality_score = self._calculate_quality_score(
            rms_level, peak_level, duration, voice_activity_ratio, 
            noise_level, dynamic_range, clipping_detected
        )
        
        return AudioQualityMetrics(
            has_voice=has_voice,
            rms_level=rms_level,
            peak_level=peak_level,
            duration=duration,
            file_size_mb=file_size_mb,
            sample_rate=sample_rate,
            channels=1,  # We convert to mono
            voice_activity_ratio=voice_activity_ratio,
            noise_level=noise_level,
            dynamic_range=dynamic_range,
            clipping_detected=clipping_detected,
            quality_score=quality_score
        )
        
    def _detect_voice_activity(self, audio_data: np.ndarray, sample_rate: int) -> list[VoiceActivitySegment]:
        """Detect voice activity segments using energy-based VAD"""
        try:
            # Frame-based analysis
            frame_duration = 0.025  # 25ms frames
            frame_shift = 0.010     # 10ms shift
            
            frame_length = int(frame_duration * sample_rate)
            frame_shift_samples = int(frame_shift * sample_rate)
            
            # Calculate RMS energy for each frame
            frame_energies = []
            for i in range(0, len(audio_data) - frame_length, frame_shift_samples):
                frame = audio_data[i:i + frame_length]
                energy = np.sqrt(np.mean(frame**2))
                frame_energies.append(energy)
                
            frame_energies = np.array(frame_energies)
            
            # Adaptive threshold based on energy distribution (optimized sensitivity)
            energy_threshold = max(
                self.voice_threshold_rms,
                np.percentile(frame_energies, 40)  # 40th percentile as threshold (more sensitive)
            )
            
            # Detect voice segments
            voice_frames = frame_energies > energy_threshold
            
            # Convert frame-based detection to time-based segments
            segments = []
            in_voice_segment = False
            segment_start = 0
            
            for i, is_voice in enumerate(voice_frames):
                time_pos = i * frame_shift
                
                if is_voice and not in_voice_segment:
                    # Start of voice segment
                    in_voice_segment = True
                    segment_start = time_pos
                    
                elif not is_voice and in_voice_segment:
                    # End of voice segment
                    segment_duration = time_pos - segment_start
                    if segment_duration >= 0.1:  # Minimum 100ms segment
                        confidence = float(np.mean(frame_energies[
                            max(0, int(segment_start / frame_shift)):
                            min(len(frame_energies), int(time_pos / frame_shift))
                        ]) / energy_threshold)
                        
                        segments.append(VoiceActivitySegment(
                            start_time=segment_start,
                            end_time=time_pos,
                            duration=segment_duration,
                            confidence=min(1.0, confidence)
                        ))
                    
                    in_voice_segment = False
                    
            # Handle case where recording ends during voice segment
            if in_voice_segment:
                final_time = len(audio_data) / sample_rate
                segment_duration = final_time - segment_start
                if segment_duration >= 0.1:
                    confidence = float(np.mean(frame_energies[
                        int(segment_start / frame_shift):
                    ]) / energy_threshold)
                    
                    segments.append(VoiceActivitySegment(
                        start_time=segment_start,
                        end_time=final_time,
                        duration=segment_duration,
                        confidence=min(1.0, confidence)
                    ))
                    
            return segments
            
        except Exception as e:
            self.logger.warning(f"Voice activity detection failed: {e}")
            # Fallback: create single segment if RMS is above threshold
            rms = np.sqrt(np.mean(audio_data**2))
            duration = len(audio_data) / sample_rate
            
            if rms > self.voice_threshold_rms and duration >= self.min_duration:
                return [VoiceActivitySegment(
                    start_time=0,
                    end_time=duration,
                    duration=duration,
                    confidence=min(1.0, rms / self.voice_threshold_rms)
                )]
            else:
                return []
                
    def _calculate_voice_ratio(self, segments: list[VoiceActivitySegment], total_duration: float) -> float:
        """Calculate the ratio of voice activity to total duration"""
        if not segments or total_duration <= 0:
            return 0.0
            
        total_voice_time = sum(segment.duration for segment in segments)
        return min(1.0, total_voice_time / total_duration)
        
    def _estimate_noise_level(self, audio_data: np.ndarray) -> float:
        """Estimate background noise level"""
        try:
            # Use lower percentile of RMS values as noise floor
            frame_size = 1024
            rms_values = []
            
            for i in range(0, len(audio_data) - frame_size, frame_size // 2):
                frame = audio_data[i:i + frame_size]
                rms = np.sqrt(np.mean(frame**2))
                rms_values.append(rms)
                
            if rms_values:
                return float(np.percentile(rms_values, self.noise_floor_percentile))
            else:
                return 0.0
                
        except Exception as e:
            self.logger.warning(f"Noise level estimation failed: {e}")
            return 0.0
            
    def _calculate_dynamic_range(self, audio_data: np.ndarray) -> float:
        """Calculate dynamic range in dB"""
        try:
            peak = np.max(np.abs(audio_data))
            rms = np.sqrt(np.mean(audio_data**2))
            
            if rms > 0 and peak > 0:
                dynamic_range_db = 20 * np.log10(peak / rms)
                return float(dynamic_range_db)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.warning(f"Dynamic range calculation failed: {e}")
            return 0.0
            
    def _calculate_quality_score(self, rms_level: float, peak_level: float, duration: float,
                               voice_activity_ratio: float, noise_level: float, 
                               dynamic_range: float, clipping_detected: bool) -> float:
        """Calculate overall audio quality score (0-100)"""
        try:
            score = 100.0
            
            # Penalize very low or very high RMS levels
            if rms_level < 0.01:
                score -= 30  # Too quiet
            elif rms_level > 0.5:
                score -= 20  # Too loud
                
            # Penalize short duration
            if duration < 1.0:
                score -= 20 * (1.0 - duration)
                
            # Reward good voice activity ratio
            if voice_activity_ratio > 0.5:
                score += 10
            elif voice_activity_ratio < 0.1:
                score -= 30
                
            # Penalize high noise levels
            if noise_level > rms_level * 0.5:
                score -= 25
                
            # Penalize poor dynamic range
            if dynamic_range < 6.0:  # Less than 6dB dynamic range
                score -= 15
                
            # Penalize clipping
            if clipping_detected:
                score -= 20
                
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            self.logger.warning(f"Quality score calculation failed: {e}")
            return 50.0  # Default middle score
            
    def get_validation_message(self, metrics: AudioQualityMetrics) -> Tuple[str, str]:
        """Get user-friendly validation message based on metrics"""
        if not metrics.has_voice:
            if metrics.duration < self.min_duration:
                return "Recording too short", f"Please record for at least {self.min_duration:.1f} seconds."
                
            elif metrics.rms_level < self.silence_threshold_rms:
                return "No audio detected", "Your recording appears to be silent. Please check your microphone."
                
            elif metrics.voice_activity_ratio < 0.1:
                return "No voice detected", "No speech was detected in your recording. Please speak clearly into the microphone."
                
            elif metrics.noise_level > metrics.rms_level * 0.8:
                return "Too much noise", "Your recording contains mostly noise. Please try recording in a quieter environment."
                
            else:
                return "Audio quality issue", "The recording quality is too low for transcription. Please try again."
                
        else:
            # Audio is valid, but provide quality feedback
            if metrics.quality_score >= 80:
                return "Excellent quality", "Audio quality is excellent for transcription."
            elif metrics.quality_score >= 60:
                return "Good quality", "Audio quality is good for transcription."
            elif metrics.quality_score >= 40:
                return "Fair quality", "Audio quality is acceptable but could be improved."
            else:
                return "Low quality", "Audio quality is low. Consider improving recording conditions."


# Global validator instance
_audio_validator = AudioValidator()


def validate_audio_file(file_path: str, 
                       custom_thresholds: Optional[dict] = None) -> AudioQualityMetrics:
    """Validate an audio file with optional custom thresholds"""
    validator = _audio_validator
    
    if custom_thresholds:
        # Temporarily update thresholds
        original_thresholds = {}
        for key, value in custom_thresholds.items():
            if hasattr(validator, key):
                original_thresholds[key] = getattr(validator, key)
                setattr(validator, key, value)
                
        try:
            return validator.validate_audio_file(file_path)
        finally:
            # Restore original thresholds
            for key, value in original_thresholds.items():
                setattr(validator, key, value)
    else:
        return validator.validate_audio_file(file_path)


def get_validation_message(metrics: AudioQualityMetrics) -> Tuple[str, str]:
    """Get user-friendly validation message"""
    return _audio_validator.get_validation_message(metrics)