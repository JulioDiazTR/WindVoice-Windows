# WindVoice-Windows Development Guide

## Development Setup

### Prerequisites

- **Python 3.11+** (recommended: 3.11 or 3.12)
- **Windows 10+** (required for Windows-specific dependencies)
- **Git** for version control
- **Visual Studio Code** (recommended IDE)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd WindVoice-Windows
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies** (when available)
   ```bash
   # Development dependencies not yet implemented
   # pip install -r requirements-dev.txt
   ```

5. **Configure environment**
   ```bash
   # Configuration will be created automatically on first run
   # Edit ~/.windvoice/config.toml with your LiteLLM credentials
   ```

### IDE Configuration

#### Visual Studio Code Setup

**Recommended Extensions:**
- Python (Microsoft)
- Pylance (Microsoft) 
- Python Docstring Generator
- Black Formatter
- isort

**Settings (.vscode/settings.json):**
```json
{
    "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.autoSave": "onDelay",
    "editor.formatOnSave": true
}
```

## Development Workflow

### Running the Application

```bash
# Development mode (with console output)
python main.py

# Alternative entry point
python run_windvoice.py

# Direct module execution
python -m windvoice.core.app
```

### Configuration Management

**Configuration Location:**
- User config: `%USERPROFILE%\.windvoice\config.toml`
- Auto-created on first run with default values

**Required Configuration:**
```toml
[litellm]
api_key = "sk-your-key-here"
api_base = "https://your-proxy.com"
key_alias = "your-username"
model = "whisper-1"

[app]
hotkey = "ctrl+shift+space"
audio_device = "default"
sample_rate = 44100

[ui]
theme = "dark"
window_position = "center"
show_tray_notifications = true
```

### Common Development Tasks

#### 1. Testing Audio Recording

```python
from windvoice.services.audio import AudioRecorder

# Test audio recording
recorder = AudioRecorder()
recorder.start_recording()
# Speak into microphone
audio_file = recorder.stop_recording()
print(f"Audio saved to: {audio_file}")
```

#### 2. Testing Audio Validation

```python
from windvoice.utils.audio_validation import validate_audio_file

# Test audio validation
metrics = validate_audio_file("path/to/audio.wav")
print(f"Has voice: {metrics.has_voice}")
print(f"Quality score: {metrics.quality_score}")
```

#### 3. Testing LiteLLM Connection

```python
from windvoice.core.config import ConfigManager
from windvoice.services.transcription import TranscriptionService

config = ConfigManager().load_config()
service = TranscriptionService(config.litellm)

# Test connection
success, message = await service.test_connection()
print(f"Connection test: {'✅' if success else '❌'} {message}")
```

### Debugging

#### Enable Debug Logging

**Method 1: Environment Variable**
```bash
set WINDVOICE_LOG_LEVEL=DEBUG
python main.py
```

**Method 2: Code Modification**
```python
# In windvoice/core/app.py, line 24:
self.logger = setup_logging("DEBUG", True)  # Force debug mode
```

#### Debug Hotkey Issues

```python
# Test hotkey without full app
from windvoice.services.hotkeys import HotkeyManager
import asyncio

async def test_hotkey():
    manager = HotkeyManager()
    manager.set_hotkey("ctrl+shift+space")
    manager.set_hotkey_callback(lambda: print("Hotkey pressed!"))
    manager.start(asyncio.get_event_loop())
    
    # Keep running
    while True:
        await asyncio.sleep(1)

asyncio.run(test_hotkey())
```

#### Debug Audio Issues

```bash
# List audio devices
python -c "
from windvoice.services.audio import AudioRecorder
recorder = AudioRecorder()
devices = recorder.list_audio_devices()
for i, device in enumerate(devices):
    print(f'{i}: {device}')
"
```

## Code Structure Guidelines

### Package Organization

```
src/windvoice/
├── core/               # Core application logic
│   ├── app.py          # Main application controller
│   ├── config.py       # Configuration management
│   └── exceptions.py   # Custom exceptions
├── services/           # Business logic services
│   ├── audio.py        # Audio recording
│   ├── transcription.py # LiteLLM integration
│   ├── injection.py    # Text injection
│   └── hotkeys.py      # Global hotkeys
├── ui/                 # User interface components
│   ├── menubar.py      # System tray
│   ├── settings.py     # Settings window
│   ├── popup.py        # Result popups
│   └── status_dialog.py # Status dialogs
└── utils/              # Utility modules
    ├── audio_validation.py # Audio analysis
    ├── logging.py      # Logging configuration
    └── windows.py      # Windows-specific utilities
```

### Coding Standards

#### 1. Type Hints

**Always use type hints:**
```python
from typing import Optional, List, Tuple

def transcribe_audio(self, file_path: str) -> str:
    """Transcribe audio file to text."""
    pass

async def async_function(data: dict) -> Optional[str]:
    """Example async function with type hints."""
    pass
```

#### 2. Error Handling

**Use specific exceptions:**
```python
from windvoice.core.exceptions import AudioError, TranscriptionError

def risky_operation():
    try:
        # Operation that might fail
        pass
    except SpecificError as e:
        raise AudioError(f"Audio operation failed: {e}")
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error: {e}")
        raise WindVoiceError("Unexpected error occurred")
```

#### 3. Logging

**Use structured logging:**
```python
from windvoice.utils.logging import get_logger, WindVoiceLogger

class MyService:
    def __init__(self):
        self.logger = get_logger("my_service")
    
    def do_something(self):
        self.logger.info("Starting operation")
        
        # Use workflow logging for complex operations
        WindVoiceLogger.log_audio_workflow_step(
            self.logger,
            "Operation_Started",
            {"parameter": "value"}
        )
```

#### 4. Configuration

**Service configuration pattern:**
```python
@dataclass
class ServiceConfig:
    param1: str
    param2: int = 100
    param3: bool = True

class MyService:
    def __init__(self, config: ServiceConfig):
        self.config = config
        
    def validate_config(self) -> bool:
        """Validate service configuration."""
        return bool(self.config.param1)
```

#### 5. Async/Await Patterns

**Proper async service patterns:**
```python
class AsyncService:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/windvoice --cov-report=html

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only

# Run with verbose output
pytest tests/ -v

# Run specific test
pytest tests/unit/test_audio_validation.py -v
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from windvoice.services.audio import AudioRecorder
from windvoice.core.exceptions import AudioError

class TestAudioRecorder:
    def test_audio_recorder_initialization(self):
        """Test AudioRecorder initializes correctly."""
        recorder = AudioRecorder(sample_rate=44100, device="default")
        assert recorder.sample_rate == 44100
        assert recorder.device == "default"
    
    @patch('sounddevice.rec')
    def test_start_recording(self, mock_rec):
        """Test recording starts correctly."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        assert recorder.is_recording()
        mock_rec.assert_called_once()
    
    def test_validation_with_invalid_file(self):
        """Test validation with non-existent file."""
        recorder = AudioRecorder()
        with pytest.raises(AudioError):
            recorder.get_quality_metrics("nonexistent.wav")
```

#### Integration Test Example

```python
import pytest
import asyncio
from pathlib import Path
from windvoice.core.app import WindVoiceApp

@pytest.mark.asyncio
class TestFullWorkflow:
    async def test_complete_workflow(self, temp_audio_file):
        """Test complete recording -> transcription -> injection workflow."""
        app = WindVoiceApp()
        
        # Mock external dependencies
        with patch('windvoice.services.transcription.aiohttp.ClientSession'):
            await app.initialize()
            
            # Simulate workflow
            result = await app._handle_transcription_result("Test text")
            assert result is not None
```

### Test Fixtures

**Conftest.py setup:**
```python
import pytest
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

@pytest.fixture
def temp_audio_file():
    """Create temporary audio file for testing."""
    # Generate 1-second sine wave
    duration = 1.0
    sample_rate = 44100
    frequency = 440  # A note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        sf.write(f.name, audio_data, sample_rate)
        yield f.name
        
    # Cleanup
    Path(f.name).unlink(missing_ok=True)

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    from windvoice.core.config import WindVoiceConfig, LiteLLMConfig, AppConfig, UIConfig
    
    return WindVoiceConfig(
        litellm=LiteLLMConfig(
            api_key="test-key",
            api_base="https://test.com",
            key_alias="test-user",
            model="whisper-1"
        ),
        app=AppConfig(),
        ui=UIConfig()
    )
```

## Maintenance Procedures

### Code Quality Checks

```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Run linting
pylint src/windvoice/

# Type checking
mypy src/windvoice/
```

### Performance Monitoring

#### Memory Usage Tracking

```python
import psutil
import os

def monitor_memory():
    """Monitor application memory usage."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.1f} MB")

# Add to main application loop
```

#### Performance Profiling

```python
import cProfile
import pstats

def profile_startup():
    """Profile application startup."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run application initialization
    app = WindVoiceApp()
    asyncio.run(app.initialize())
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

### Dependency Management

#### Updating Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements file
pip freeze > requirements.txt
```

#### Security Considerations

- Review dependencies regularly for security updates
- Use virtual environments to isolate dependencies
- Consider using tools like `pip-audit` for security scanning

### Release Procedures

#### Version Management

**Update version in:**
- `src/windvoice/__init__.py` (when version file is created)
- `docs/PRD.md`
- `README.md`

```python
# Version management to be implemented
# __version__ = "2.1.0"
```

#### Pre-release Checklist (Future)

- [ ] Test suite implementation completed
- [ ] Code formatted and linted
- [ ] Documentation updated
- [ ] Version management implemented
- [ ] Performance benchmarks created
- [ ] Windows compatibility verified

#### Build Process

```bash
# Build system not yet implemented
# Planned for Sprint 3:
# pip install pyinstaller
# python scripts/build.py  # (to be created)
```

### Troubleshooting Common Issues

#### 1. Audio Recording Issues

**Problem**: No audio devices detected
```bash
# Diagnostic commands
python -c "import sounddevice; print(sounddevice.query_devices())"
```

**Solution**: Install/update audio drivers, check Windows audio settings

#### 2. LiteLLM Connection Issues

**Problem**: API connection failures
```python
# Test connection
from windvoice.services.transcription import TranscriptionService
# Check logs for detailed error information
```

**Solution**: Verify API credentials, check network connectivity

#### 3. Hotkey Not Working

**Problem**: Global hotkey not responding
**Solution**: Check for hotkey conflicts, run as administrator if needed

#### 4. Memory Leaks

**Problem**: Memory usage increasing over time
**Solution**: 
- Check audio buffer cleanup
- Verify HTTP session closure
- Monitor with memory profiling tools

### Development Best Practices

#### 1. Branch Strategy

- `main`: Stable production code
- `develop`: Integration branch
- `feature/*`: Feature development
- `hotfix/*`: Critical bug fixes

#### 2. Commit Messages

Follow conventional commit format:
```
type(scope): description

feat(audio): add real-time level monitoring
fix(transcription): resolve session cleanup issue
docs(api): update LiteLLM integration guide
```

#### 3. Code Review Checklist

- [ ] Type hints added
- [ ] Error handling implemented
- [ ] Tests written/updated
- [ ] Documentation updated
- [ ] Performance impact considered
- [ ] Windows compatibility verified

#### 4. Logging Standards

- Use appropriate log levels
- Include context information
- Never log sensitive data (API keys)
- Use structured logging for complex operations

This development guide provides comprehensive information for maintaining and extending the WindVoice-Windows application. Follow these guidelines to ensure code quality, performance, and maintainability.