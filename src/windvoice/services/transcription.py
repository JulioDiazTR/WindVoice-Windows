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
        
        url = f"{self.config.api_base}/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Key-Alias": self.config.key_alias
        }
        
        # Retry logic - 3 attempts with 1-second delays
        for attempt in range(3):
            try:
                session = await self._get_session()
                
                # Create form data for file upload
                data = aiohttp.FormData()
                with open(audio_file_path, 'rb') as audio_file:
                    audio_content = audio_file.read()
                    
                data.add_field(
                    'file',
                    audio_content,
                    filename='audio.wav',
                    content_type='audio/wav'
                )
                data.add_field('model', self.config.model)
                data.add_field('response_format', 'json')
                
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('text', '').strip()
                    
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
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()