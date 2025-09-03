import aiohttp
import asyncio
from pathlib import Path
from typing import Optional
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
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        if not Path(audio_file_path).exists():
            raise TranscriptionError(f"Audio file not found: {audio_file_path}")
        
        # CRITICAL FIX: Force fresh session for each transcription to prevent caching
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None
        
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
            "Cache-Control": "no-cache"  # Prevent caching
        }
        
        # Log detailed request information
        file_size = Path(audio_file_path).stat().st_size
        self.logger.info(f"[TRANSCRIPTION_REQUEST] ID: {request_id}, File: {audio_file_path}, Size: {file_size} bytes")
        
        # Retry logic - 3 attempts with 1-second delays
        for attempt in range(3):
            try:
                session = await self._get_session()
                
                # Create form data for file upload
                data = aiohttp.FormData()
                with open(audio_file_path, 'rb') as audio_file:
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
                        
                        # Force session cleanup after successful transcription
                        await session.close()
                        self.session = None
                        
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