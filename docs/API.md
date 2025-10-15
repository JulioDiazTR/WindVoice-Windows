# WindVoice-Windows API Integration Documentation

## Overview

WindVoice-Windows integrates with Thomson Reuters LiteLLM proxy to provide AI-powered speech transcription using OpenAI's Whisper-1 model. This document covers the complete API integration, authentication, error handling, and best practices.

## LiteLLM Integration Architecture

### Service Overview

```
WindVoice Application
        ↓
   HTTP Request (aiohttp)
        ↓
Thomson Reuters LiteLLM Proxy
        ↓
    OpenAI Whisper-1 API
        ↓
   Transcription Response
```

### Configuration

**Configuration file:** `%USERPROFILE%\.windvoice\config.toml`

**Required fields:** `api_key`, `api_base`, `key_alias`, `model`

**See:** [config.example.toml](config.example.toml) for complete configuration template with descriptions

**Validation:**
```python
from windvoice.core.config import ConfigManager
config_manager = ConfigManager()
is_valid = config_manager.validate_config()
```

## API Endpoints

### Audio Transcription

**Endpoint:** `POST /v1/audio/transcriptions`

**Purpose:** Convert audio files to text using OpenAI's Whisper-1 model

#### Request Format

```http
POST https://your-proxy.com/v1/audio/transcriptions
Content-Type: multipart/form-data

Headers:
  Authorization: Bearer sk-your-api-key
  X-Key-Alias: your-username
  X-Request-ID: unique-request-identifier
  Cache-Control: no-cache

Form Data:
  file: audio_timestamp_requestid.wav (binary audio data)
  model: whisper-1
  response_format: json
  timestamp: 1698765432000
```

#### Response Format

**Success Response (200 OK):**
```json
{
  "text": "The transcribed text from the audio file."
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request format or missing parameters
- `401 Unauthorized`: Invalid API key or authentication failure
- `413 Payload Too Large`: Audio file exceeds size limits
- `429 Too Many Requests`: Rate limit exceeded
- `503 Service Unavailable`: Temporary service unavailability

## Implementation Details

### TranscriptionService Class

The `TranscriptionService` class in `src/windvoice/services/transcription.py` handles all LiteLLM API interactions.

#### Initialization

```python
from windvoice.services.transcription import TranscriptionService
from windvoice.core.config import LiteLLMConfig

# Create service instance
config = LiteLLMConfig(
    api_key="sk-your-key",
    api_base="https://your-proxy.com",
    key_alias="your-username",
    model="whisper-1"
)

service = TranscriptionService(config)
```

#### Core Methods

##### transcribe_audio()

Main transcription method with retry logic and error handling.

```python
async def transcribe_audio(self, audio_file_path: str) -> str:
    """
    Transcribe audio file using LiteLLM proxy.
    
    Args:
        audio_file_path: Path to WAV audio file
        
    Returns:
        Transcribed text string
        
    Raises:
        TranscriptionError: On API errors or failures
    """
```

**Implementation Features:**
- **Fresh Session Management**: New HTTP session for each request
- **Request Uniqueness**: UUID-based request IDs and timestamps
- **Retry Logic**: 3 attempts with 1-second delays
- **Error Classification**: Specific handling for different HTTP status codes

##### test_connection()

Validates API connectivity and authentication.

```python
async def test_connection(self) -> tuple[bool, str]:
    """
    Test LiteLLM API connection.
    
    Returns:
        (success: bool, message: str)
    """
    
# Usage example
success, message = await service.test_connection()
if success:
    print("✅ API connection successful")
else:
    print(f"❌ Connection failed: {message}")
```

### Request Implementation

#### Unique Request Generation

To prevent server-side caching and ensure fresh responses:

```python
import time
import uuid

# Generate unique identifiers
request_id = str(uuid.uuid4())[:8]
timestamp = int(time.time() * 1000)  # milliseconds

# Create unique filename
unique_filename = f'audio_{timestamp}_{request_id}.wav'

# Add to form data
data = aiohttp.FormData()
data.add_field(
    'file',
    audio_content,
    filename=unique_filename,
    content_type='audio/wav'
)
data.add_field('model', 'whisper-1')
data.add_field('response_format', 'json')
data.add_field('timestamp', str(timestamp))
```

#### HTTP Session Management

```python
class TranscriptionService:
    def __init__(self, config: LiteLLMConfig):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper configuration."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        # Force fresh session for each transcription
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None
        
        # Create new session for this request
        session = await self._get_session()
        # ... transcription logic
```

### Error Handling

#### Exception Hierarchy

```python
# Base exception
class TranscriptionError(WindVoiceError):
    """Base exception for transcription errors"""
    pass

# Specific error types (defined implicitly by status codes)
# 401 → "API key is invalid"
# 503 → "Service temporarily unavailable" 
# Network errors → "Check internet connection"
```

#### Error Classification

```python
async def transcribe_audio(self, audio_file_path: str) -> str:
    try:
        # Make API request
        async with session.post(url, headers=headers, data=data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('text', '').strip()
            
            elif response.status == 401:
                raise TranscriptionError(
                    "API key is invalid. Please check your LiteLLM settings."
                )
            
            elif response.status == 503:
                if attempt < 2:  # Retry on service unavailable
                    await asyncio.sleep(1)
                    continue
                raise TranscriptionError(
                    "Transcription service is temporarily unavailable."
                )
            
            else:
                error_text = await response.text()
                raise TranscriptionError(
                    f"Transcription failed (HTTP {response.status})"
                )
                
    except aiohttp.ClientError as e:
        raise TranscriptionError(
            "Network error. Please check your internet connection."
        )
```

### Retry Logic

The service implements intelligent retry logic for handling temporary failures:

```python
# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

for attempt in range(MAX_RETRIES):
    try:
        # Attempt API call
        result = await make_api_call()
        return result
        
    except TransientError:
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAY)
            continue
        raise
        
    except PermanentError:
        # Don't retry permanent errors
        raise
```

**Retry Scenarios:**
- ✅ HTTP 503 (Service Unavailable)
- ✅ Network timeouts
- ✅ Connection errors
- ❌ HTTP 401 (Authentication failure)
- ❌ HTTP 400 (Bad request)

### Logging and Monitoring

#### Request Logging

```python
# Log request details
file_size = Path(audio_file_path).stat().st_size
self.logger.info(
    f"[TRANSCRIPTION_REQUEST] ID: {request_id}, "
    f"File: {audio_file_path}, Size: {file_size} bytes"
)

# Log response details
self.logger.info(
    f"[TRANSCRIPTION_RESPONSE] ID: {request_id}, "
    f"Status: 200, Text: '{transcribed_text}', "
    f"Length: {len(transcribed_text)}"
)
```

#### Security Considerations

**Never log sensitive information:**
```python
# ❌ NEVER do this
self.logger.debug(f"API Key: {self.config.api_key}")

# ✅ Safe logging
self.logger.debug(f"API Key configured: {'Yes' if self.config.api_key else 'No'}")
self.logger.debug(f"API Key: {self.config.api_key[:10]}...{self.config.api_key[-4:]}")
```

## Audio Requirements

### Format Specifications

The LiteLLM integration expects high-quality WAV files optimized for Whisper:

**Required Format:**
- **Container**: WAV (RIFF)
- **Sample Rate**: 44,100 Hz
- **Bit Depth**: 16-bit
- **Channels**: Mono (1 channel)
- **Encoding**: PCM (uncompressed)

**File Size Limits:**
- **Maximum**: ~25MB (typical for Whisper)
- **Typical Range**: 100KB - 5MB for voice recordings
- **Duration**: 0.3 - 30 seconds (optimal for voice dictation)

### Audio Validation Integration

Before sending to LiteLLM, audio is validated using the AudioValidator:

```python
from windvoice.utils.audio_validation import validate_audio_file

# Validate before transcription
metrics = validate_audio_file(audio_file_path)

if not metrics.has_voice:
    # Don't waste API calls on silent audio
    self.logger.info("Skipping transcription - no voice detected")
    return ""

# Only send quality audio to API
if metrics.quality_score < 40:
    self.logger.warning(f"Low quality audio (score: {metrics.quality_score})")
```

## Usage Examples

### Basic Transcription

```python
from windvoice.services.transcription import TranscriptionService

# Initialize service
service = TranscriptionService(config.litellm)

# Test connection
success, message = await service.test_connection()

# Transcribe audio
text = await service.transcribe_audio("recording.wav")
```

**Complete Examples:** See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed testing examples and workflow integration

## Performance Considerations

### API Optimization

1. **Fresh Sessions**: New HTTP session per request prevents connection reuse issues
2. **Request Uniqueness**: Timestamps and UUIDs prevent server-side caching
3. **Timeout Configuration**: 30-second timeout for API requests
4. **Connection Cleanup**: Explicit session closure after each request

### Cost Optimization

1. **Audio Validation**: Skip API calls for silent/low-quality audio
2. **File Size Optimization**: Use efficient WAV encoding
3. **Duration Limits**: Optimal 0.3-30 second audio clips
4. **Quality Thresholds**: Only transcribe audio with sufficient quality scores

### Rate Limiting

The service handles rate limiting gracefully:
- Detects HTTP 429 (Too Many Requests) responses
- Implements exponential backoff for retries
- Logs rate limit encounters for monitoring

## Security Best Practices

### Credential Management

1. **Storage**: Configuration stored in user home directory
2. **Access Control**: File system permissions only
3. **No Hardcoding**: Never embed credentials in code
4. **Environment Variables**: Support for env var configuration

### Data Security

1. **Transport**: HTTPS only with certificate validation
2. **Temporary Files**: Automatic cleanup of audio files
3. **Logging**: Never log API keys or sensitive data
4. **Request IDs**: Use for debugging without exposing content

### Error Information

1. **User Messages**: Generic, user-friendly error messages
2. **Debug Logs**: Detailed error information for developers
3. **Sensitive Data**: Never expose API keys in error messages

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptoms:**
- HTTP 401 responses
- "Invalid API key" errors

**Diagnosis:**
```python
# Test API key format
if not config.api_key.startswith("sk-"):
    print("❌ API key should start with 'sk-'")

# Test connection
success, message = await service.test_connection()
print(f"Connection test: {message}")
```

**Solutions:**
- Verify API key from Thomson Reuters admin
- Check key_alias matches your user identifier
- Ensure api_base URL is correct

#### 2. Network Issues

**Symptoms:**
- Connection timeout errors
- "Network error" messages

**Diagnosis:**
```bash
# Test connectivity
curl -I https://your-proxy.com/v1/models

# Check DNS resolution
nslookup your-proxy.com
```

**Solutions:**
- Check internet connectivity
- Verify proxy URL accessibility
- Check corporate firewall settings

#### 3. Audio Format Issues

**Symptoms:**
- HTTP 400 responses
- "Invalid audio format" errors

**Diagnosis:**
```python
# Check audio file format
import soundfile as sf
info = sf.info(audio_file_path)
print(f"Format: {info.format}")
print(f"Sample rate: {info.samplerate}")
print(f"Channels: {info.channels}")
```

**Solutions:**
- Ensure 44.1kHz sample rate
- Convert to mono channel
- Use WAV container format

#### 4. Service Unavailability

**Symptoms:**
- HTTP 503 responses
- Intermittent failures

**Diagnosis:**
```python
# Monitor service status
for i in range(5):
    success, message = await service.test_connection()
    print(f"Attempt {i+1}: {'✅' if success else '❌'} {message}")
    await asyncio.sleep(2)
```

**Solutions:**
- Implement retry logic (already included)
- Check service status with Thomson Reuters
- Consider alternative models if available

This API documentation provides comprehensive coverage of the LiteLLM integration, enabling developers to maintain, extend, and troubleshoot the transcription service effectively.