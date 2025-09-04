import aiohttp
import asyncio
import tempfile
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from ..core.exceptions import TranscriptionError
from ..core.config import LiteLLMConfig
from ..utils.logging import get_logger, WindVoiceLogger


class TranscriptionService:
    def __init__(self, config: LiteLLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = get_logger("transcription")
        
        # Log initialization
        self.logger.info("TranscriptionService initialized")
        self.logger.debug(f"API Base: {config.api_base}")
        self.logger.debug(f"Model: {config.model}")
        self.logger.debug(f"Key Alias: {config.key_alias}")
        self.logger.debug(f"API Key configured: {'Yes' if config.api_key else 'No'}")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15, connect=5)
            )
        return self.session
    
    def _compress_audio_if_needed(self, audio_file_path: str) -> Tuple[str, bool]:
        """Compress audio file if it's larger than 10MB to optimize API performance"""
        file_path = Path(audio_file_path)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # If file is smaller than 10MB, no compression needed
        if file_size_mb <= 10.0:
            self.logger.debug(f"Audio file size {file_size_mb:.1f}MB <= 10MB, no compression needed")
            return audio_file_path, False
            
        self.logger.info(f"Audio file size {file_size_mb:.1f}MB > 10MB, applying compression...")
        
        try:
            # Load audio data
            audio_data, sample_rate = sf.read(audio_file_path)
            
            # Ensure mono
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Compress: reduce sample rate to 22kHz (optimal for speech)
            if sample_rate > 22050:
                from scipy import signal
                # Calculate decimation factor
                decimation_factor = sample_rate // 22050
                if decimation_factor > 1:
                    # Apply anti-aliasing filter and downsample
                    audio_data = signal.decimate(audio_data, decimation_factor, ftype='iir')
                    new_sample_rate = sample_rate // decimation_factor
                    self.logger.debug(f"Downsampled from {sample_rate}Hz to {new_sample_rate}Hz")
                else:
                    new_sample_rate = sample_rate
            else:
                new_sample_rate = sample_rate
            
            # Create compressed file
            compressed_path = file_path.parent / f"compressed_{file_path.name}"
            
            # Save with optimized settings for speech transcription
            sf.write(
                str(compressed_path),
                audio_data,
                new_sample_rate,
                subtype='PCM_16'  # 16-bit PCM for optimal size/quality balance
            )
            
            compressed_size_mb = compressed_path.stat().st_size / (1024 * 1024)
            compression_ratio = file_size_mb / compressed_size_mb
            
            self.logger.info(f"Audio compressed: {file_size_mb:.1f}MB → {compressed_size_mb:.1f}MB "
                           f"(ratio: {compression_ratio:.1f}x)")
            
            return str(compressed_path), True
            
        except Exception as e:
            self.logger.warning(f"Audio compression failed: {e}, using original file")
            return audio_file_path, False
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        if not Path(audio_file_path).exists():
            raise TranscriptionError(f"Audio file not found: {audio_file_path}")
        
        # Compress audio if needed for optimal API performance
        working_file_path, was_compressed = self._compress_audio_if_needed(audio_file_path)
        
        # Optimized session management: keep session alive but force fresh request
        # Note: We keep the session but ensure each request is unique to prevent caching issues
        
        # Generate unique identifier for this request
        import time
        import uuid
        request_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time() * 1000)  # milliseconds
        
        url = f"{self.config.api_base}/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Key-Alias": self.config.key_alias,
            "X-Request-ID": request_id,  # Unique identifier
            "X-Timestamp": str(timestamp),  # Ensure uniqueness
            "Cache-Control": "no-cache, no-store, must-revalidate",  # Prevent caching
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        # Log detailed request information
        file_size = Path(working_file_path).stat().st_size
        self.logger.info(f"[TRANSCRIPTION_REQUEST] ID: {request_id}, File: {working_file_path}, Size: {file_size} bytes, Compressed: {was_compressed}")
        
        # Retry logic - 3 attempts with 1-second delays
        for attempt in range(3):
            try:
                session = await self._get_session()
                
                # Create form data for file upload
                data = aiohttp.FormData()
                with open(working_file_path, 'rb') as audio_file:
                    audio_content = audio_file.read()
                    
                # Add unique filename with timestamp to prevent server-side caching
                unique_filename = f'audio_{timestamp}_{request_id}.wav'
                data.add_field(
                    'file',
                    audio_content,
                    filename=unique_filename,
                    content_type='audio/wav'
                )
                data.add_field('model', self.config.model)
                data.add_field('response_format', 'json')
                data.add_field('timestamp', str(timestamp))  # Force unique request
                
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        transcribed_text = result.get('text', '').strip()
                        
                        # Log detailed response information
                        self.logger.info(f"[TRANSCRIPTION_RESPONSE] ID: {request_id}, Status: 200, Text: '{transcribed_text}', Length: {len(transcribed_text)}")
                        
                        # Keep session alive for better performance (don't close unnecessarily)
                        
                        # Clean up compressed file if it was created
                        if was_compressed and Path(working_file_path).exists():
                            try:
                                Path(working_file_path).unlink()
                                self.logger.debug(f"Cleaned up compressed file: {working_file_path}")
                            except Exception as cleanup_error:
                                self.logger.warning(f"Failed to clean up compressed file: {cleanup_error}")
                        
                        return transcribed_text
                    
                    elif response.status == 401:
                        error_text = await response.text()
                        raise TranscriptionError("API key is invalid. Please check your LiteLLM settings.")
                    
                    elif response.status == 503:
                        if attempt < 2:  # Retry on service unavailable
                            await asyncio.sleep(1)
                            continue
                        raise TranscriptionError("Transcription service is temporarily unavailable.")
                    
                    else:
                        error_text = await response.text()
                        if attempt < 2:
                            await asyncio.sleep(1)
                            continue
                        raise TranscriptionError(f"Transcription failed (HTTP {response.status})")
                        
            except aiohttp.ClientError as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                raise TranscriptionError("Network error. Please check your internet connection.")
            
            except TranscriptionError:
                raise
                
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                raise TranscriptionError(f"Transcription failed: {str(e)}")
        
        # Clean up compressed file if it was created (in case of final failure)
        if was_compressed and Path(working_file_path).exists():
            try:
                Path(working_file_path).unlink()
                self.logger.debug(f"Cleaned up compressed file after failure: {working_file_path}")
            except Exception as cleanup_error:
                self.logger.warning(f"Failed to clean up compressed file after failure: {cleanup_error}")
        
        raise TranscriptionError("Transcription failed after 3 attempts")
    
    def validate_config(self) -> bool:
        if not self.config.api_key:
            return False
        if not self.config.api_base:
            return False
        if not self.config.key_alias:
            return False
        if not self.config.model:
            return False
        return True
    
    def get_config_errors(self) -> list[str]:
        errors = []
        if not self.config.api_key:
            errors.append("LiteLLM API key is not configured")
        if not self.config.api_base:
            errors.append("LiteLLM API base URL is not configured")
        if not self.config.key_alias:
            errors.append("Key alias is not configured")
        if not self.config.model:
            errors.append("Model is not configured")
        return errors
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test the LiteLLM API connection with detailed logging"""
        self.logger.info("[TEST] Testing LiteLLM API connection...")
        
        # Validate configuration first
        config_errors = self.get_config_errors()
        if config_errors:
            error_msg = f"Configuration errors: {', '.join(config_errors)}"
            self.logger.error(f"[FAIL] {error_msg}")
            return False, error_msg
        
        try:
            # Create a minimal test request to /v1/models endpoint
            session = await self._get_session()
            test_url = f"{self.config.api_base}/v1/models"
            headers = {
                "Authorization": f"Bearer {self.config.api_key[:10]}...{self.config.api_key[-4:]}",
                "X-Key-Alias": self.config.key_alias
            }
            
            self.logger.info(f"[TEST] Testing URL: {test_url}")
            self.logger.debug(f"[TEST] Key Alias: {self.config.key_alias}")
            self.logger.debug(f"[TEST] API Key: {self.config.api_key[:10]}...{self.config.api_key[-4:]}")
            
            # Use proper headers for the actual request (don't log full API key)
            actual_headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "X-Key-Alias": self.config.key_alias
            }
            
            async with session.get(test_url, headers=actual_headers) as response:
                response_text = await response.text()
                
                self.logger.info(f"[TEST] Response Status: {response.status}")
                self.logger.debug(f"[TEST] Response: {response_text[:200]}..." if len(response_text) > 200 else response_text)
                
                if response.status == 200:
                    self.logger.info("[SUCCESS] API connection successful!")
                    return True, "Connection successful"
                elif response.status == 404:
                    # 404 is acceptable - models endpoint might not be available
                    self.logger.info("[SUCCESS] API connection successful (models endpoint not available, but auth worked)")
                    return True, "Connection successful (models endpoint not found, but authentication worked)"
                elif response.status == 401:
                    error_msg = "Invalid API key or authentication failed"
                    self.logger.error(f"[FAIL] {error_msg}")
                    return False, error_msg
                elif response.status == 403:
                    error_msg = "Access denied - check API key permissions"
                    self.logger.error(f"[FAIL] {error_msg}")
                    return False, error_msg
                else:
                    error_msg = f"Unexpected response: HTTP {response.status}"
                    self.logger.warning(f"[WARN] {error_msg}")
                    return False, error_msg
                
        except aiohttp.ClientConnectorError as e:
            error_msg = f"Connection failed - check API base URL: {str(e)}"
            self.logger.error(f"[FAIL] {error_msg}")
            return False, error_msg
        except aiohttp.ClientTimeout as e:
            error_msg = f"Request timeout - server may be slow: {str(e)}"
            self.logger.error(f"[FAIL] {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Test failed: {str(e)}"
            self.logger.error(f"[FAIL] {error_msg}")
            return False, error_msg
    
    async def get_available_models(self) -> tuple[bool, list[str], str]:
        """Get available models from LiteLLM API"""
        self.logger.info("[MODELS] Fetching available models from API...")
        
        # Validate configuration first
        config_errors = self.get_config_errors()
        if config_errors:
            error_msg = f"Configuration errors: {', '.join(config_errors)}"
            self.logger.error(f"[MODELS] {error_msg}")
            return False, [], error_msg
        
        try:
            session = await self._get_session()
            
            # Try different model endpoints that LiteLLM might support
            endpoints_to_try = [
                f"{self.config.api_base}/v1/models",
                f"{self.config.api_base}/models",
                f"{self.config.api_base}/model/info",
                f"{self.config.api_base}/v1/model/info"
            ]
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "X-Key-Alias": self.config.key_alias
            }
            
            for endpoint in endpoints_to_try:
                try:
                    self.logger.info(f"[MODELS] Trying endpoint: {endpoint}")
                    
                    async with session.get(endpoint, headers=headers) as response:
                        response_text = await response.text()
                        
                        self.logger.info(f"[MODELS] {endpoint} - Status: {response.status}")
                        self.logger.debug(f"[MODELS] Response: {response_text[:300]}...")
                        
                        if response.status == 200:
                            try:
                                result = await response.json()
                                
                                # Parse different response formats
                                models = []
                                
                                # OpenAI-style format: {"data": [{"id": "model-name"}, ...]}
                                if isinstance(result, dict) and "data" in result:
                                    models = [model.get("id", "") for model in result["data"] if model.get("id")]
                                
                                # Simple list format: ["model1", "model2", ...]
                                elif isinstance(result, list):
                                    models = [str(model) for model in result if model]
                                
                                # Direct object with models
                                elif isinstance(result, dict):
                                    # Try various keys
                                    for key in ["models", "available_models", "model_list"]:
                                        if key in result:
                                            if isinstance(result[key], list):
                                                models = [str(model) for model in result[key] if model]
                                                break
                                    
                                    # If no models found in standard keys, check if result itself contains model info
                                    if not models and "id" in result:
                                        models = [result["id"]]
                                
                                # Filter for audio/whisper models only
                                audio_models = []
                                for model in models:
                                    model_lower = model.lower()
                                    if any(keyword in model_lower for keyword in ["whisper", "speech", "audio", "transcription", "stt"]):
                                        audio_models.append(model)
                                
                                if audio_models:
                                    self.logger.info(f"[MODELS] Found {len(audio_models)} audio models: {audio_models}")
                                    return True, audio_models, f"Found {len(audio_models)} models from {endpoint}"
                                elif models:
                                    self.logger.info(f"[MODELS] Found {len(models)} total models: {models[:5]}...")
                                    return True, models, f"Found {len(models)} models from {endpoint}"
                                else:
                                    self.logger.warning(f"[MODELS] No models found in response from {endpoint}")
                                    
                            except Exception as parse_error:
                                self.logger.error(f"[MODELS] Failed to parse response from {endpoint}: {parse_error}")
                                continue
                        
                        elif response.status == 404:
                            self.logger.info(f"[MODELS] {endpoint} not available (404)")
                            continue
                        elif response.status == 401:
                            error_msg = "Invalid API key for models endpoint"
                            self.logger.error(f"[MODELS] {error_msg}")
                            return False, [], error_msg
                        else:
                            self.logger.warning(f"[MODELS] {endpoint} returned {response.status}")
                            continue
                            
                except aiohttp.ClientError as e:
                    self.logger.warning(f"[MODELS] Network error for {endpoint}: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"[MODELS] Unexpected error for {endpoint}: {e}")
                    continue
            
            # No endpoints worked
            error_msg = "No model endpoints are available or working"
            self.logger.warning(f"[MODELS] {error_msg}")
            return False, [], error_msg
            
        except Exception as e:
            error_msg = f"Failed to fetch models: {str(e)}"
            self.logger.error(f"[MODELS] {error_msg}")
            return False, [], error_msg
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()