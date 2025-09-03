# WindVoice-Windows

**Native Windows Voice Dictation Application** - Fast, accurate speech-to-text with global hotkey activation and seamless text injection.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2B-lightgrey)
![Python](https://img.shields.io/badge/python-3.11%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Table of Contents

- [Overview](#-overview)
- [Features](#-key-features)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#-usage)
- [Architecture](#️-architecture)
- [Project Structure](#-project-structure)
- [Development](#-development)
  - [Development Setup](#development-setup)
  - [Running for Development](#running-for-development)
  - [Contributing](#contributing)
- [Performance](#-performance)
- [Security](#-security)
- [Troubleshooting](#️-troubleshooting)
- [Current Status](#-current-status)
- [License](#-license)

## 🎤 Overview

WindVoice-Windows is a **100% Python** voice dictation application designed for Windows 10+ systems. It provides instant voice recording with global hotkey activation (`Ctrl+Shift+Space`) and smart text injection into any Windows application.

### ✨ Key Features

- 🔥 **Instant Hotkey Activation** - Record from any application with `Ctrl+Shift+Space`
- 🎤 **High-Quality Audio** - 44.1kHz WAV recording optimized for Whisper
- 🤖 **AI-Powered Transcription** - Thomson Reuters LiteLLM integration with OpenAI Whisper-1
- 🎯 **Smart Text Injection** - Auto-inject or popup based on context
- 🖲️ **System Tray Integration** - Lives quietly in Windows system tray
- 📊 **Real-Time Feedback** - Visual recording status and audio level monitoring
- 🔍 **Advanced Audio Validation** - Pre-transcription quality assessment
- ⚙️ **Minimal Configuration** - Simple TOML-based settings

## 🚀 Quick Start

### Prerequisites

- Windows 10 or later
- Python 3.11+ (recommended: Python 3.11 or 3.12)
- Thomson Reuters LiteLLM API credentials

### Installation

#### Option 1: Clone from Repository

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd WindVoice-Windows
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

#### Option 2: Direct Download (Future)
- Windows installer (`.msi`) - Coming in Sprint 3
- Portable executable (`.exe`) - Coming in Sprint 3

### Configuration

#### Initial Setup

On first run, WindVoice will create a configuration file at `%USERPROFILE%\.windvoice\config.toml`. You'll need to configure your Thomson Reuters LiteLLM credentials either:

1. **Through the Settings GUI** (recommended):
   - Right-click the system tray icon → Settings
   - Fill in your API credentials

2. **Edit the configuration file manually**:
   ```toml
   [litellm]
   api_key = "sk-your-litellm-api-key"
   api_base = "https://your-litellm-proxy.com"
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

#### Required LiteLLM Credentials

You'll need the following from your Thomson Reuters LiteLLM proxy:
- **API Key**: Virtual API key (format: `sk-xxxxx`)
- **API Base**: Proxy URL (format: `https://your-proxy.com`)
- **Key Alias**: Your user identifier for usage tracking

## 🎯 Usage

1. **Start WindVoice** - Application runs in system tray
2. **Press hotkey** - `Ctrl+Shift+Space` from any application
3. **Speak clearly** - Record your voice (visual feedback provided)
4. **Press hotkey again** - Stop recording
5. **Get text** - Auto-injected into active field or shown in popup

### Smart Behavior

- **Active text field detected** → Text automatically injected
- **No text field** → Popup window with transcription
- **Silent recording** → "No voice detected" notification
- **Transcription error** → Clear error message with retry option

## 🏗️ Architecture

WindVoice follows a single-process, event-driven architecture:

```
┌─────────────────────────────────────────┐
│        WindVoice Python App             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │         UI Layer                │    │
│  │  • System Tray                  │    │
│  │  • Status Dialogs               │    │
│  │  • Settings Window              │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │       Services Layer            │    │
│  │  • Audio Recording              │    │
│  │  • Audio Validation             │    │
│  │  • Transcription (LiteLLM)      │    │
│  │  • Text Injection               │    │
│  │  • Global Hotkeys               │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │         Core Layer              │    │
│  │  • Application Controller       │    │
│  │  • Configuration Management     │    │
│  │  • Exception Handling           │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
              │
              │ HTTPS API
              ▼
   ┌─────────────────────────┐
   │ Thomson Reuters         │
   │ LiteLLM Proxy          │
   │ (OpenAI Whisper-1)     │
   └─────────────────────────┘
```

### Technology Stack

- **UI Framework**: CustomTkinter 5.2.2+ (modern native UI)
- **Audio Processing**: sounddevice + soundfile + numpy
- **System Integration**: pynput (hotkeys) + pystray (system tray)
- **HTTP Client**: aiohttp (async LiteLLM integration)
- **Configuration**: TOML-based with validation

## 📁 Project Structure

```
WindVoice-Windows/
├── src/windvoice/              # Main application package
│   ├── core/                   # Core application logic
│   │   ├── app.py             # Application controller
│   │   ├── config.py          # Configuration management
│   │   └── exceptions.py      # Custom exceptions
│   ├── services/              # Business logic services
│   │   ├── audio.py           # Audio recording & validation
│   │   ├── transcription.py   # LiteLLM API integration
│   │   ├── injection.py       # Text injection service
│   │   └── hotkeys.py         # Global hotkey handling
│   ├── ui/                    # User interface components
│   │   ├── menubar.py         # System tray integration
│   │   ├── settings.py        # Settings window
│   │   ├── popup.py           # Result popups
│   │   └── status_dialog.py   # Status feedback dialogs
│   └── utils/                 # Utility modules
│       ├── audio_validation.py # Audio quality analysis
│       ├── logging.py         # Logging configuration
│       └── windows.py         # Windows-specific utilities
├── docs/                      # Comprehensive documentation
│   ├── ARCHITECTURE.md        # System architecture details
│   ├── DEVELOPMENT.md         # Development setup guide
│   ├── API.md                 # LiteLLM integration guide
│   └── PRD.md                # Product requirements
├── tests/                     # Test suite (planned for Sprint 3)
│   └── (to be implemented)
├── main.py                   # Application entry point
└── requirements.txt          # Dependencies
```

## 🔧 Development

### Development Setup

#### Prerequisites for Development
- Python 3.11+ (required)
- Windows 10+ (for Windows-specific dependencies)
- Git for version control
- Visual Studio Code (recommended IDE)

#### Setup Steps

1. **Fork and clone the repository**
   ```bash
   git clone <your-fork-url>
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
   # Development dependencies (when available)
   # pip install -r requirements-dev.txt
   ```

### Running for Development

#### Standard Development Mode
```bash
# Basic development run
python main.py

# Alternative entry point
python run_windvoice.py
```

#### Development with Debugging
```bash
# Enable debug logging
set WINDVOICE_LOG_LEVEL=DEBUG
python main.py

# Run specific tests
pytest tests/ -v

# Run with coverage (when implemented)
pytest tests/ --cov=src/windvoice
```

#### Testing Components

Test individual components during development:

```python
# Test audio recording
python -c "
from windvoice.services.audio import AudioRecorder
recorder = AudioRecorder()
devices = recorder.list_audio_devices()
for i, device in enumerate(devices):
    print(f'{i}: {device}')
"

# Test LiteLLM connection
python -c "
import asyncio
from windvoice.core.config import ConfigManager
from windvoice.services.transcription import TranscriptionService

async def test():
    config = ConfigManager().load_config()
    service = TranscriptionService(config.litellm)
    success, message = await service.test_connection()
    print(f'Connection: {'✅' if success else '❌'} {message}')

asyncio.run(test())
"
```

### Contributing

We welcome contributions! Here's how to get started:

#### 1. Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the coding standards outlined in [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)
4. Write tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

#### 2. Code Standards
- **Type hints**: Always use type annotations
- **Error handling**: Use custom exceptions from `windvoice.core.exceptions`
- **Logging**: Use the structured logging system
- **Tests**: Write unit and integration tests
- **Documentation**: Update relevant documentation

#### 3. Testing Requirements
```bash
# Run all tests (when implemented)
pytest tests/

# Run specific test categories
pytest tests/unit/          # Unit tests only  
pytest tests/integration/   # Integration tests only

# Format code before committing
black src/ tests/
isort src/ tests/
```

#### 4. Areas for Contribution
- **Testing**: Comprehensive test suite implementation
- **Performance**: Memory and CPU optimization
- **UI/UX**: Enhanced user interface features
- **Audio**: Advanced audio processing features
- **Documentation**: Tutorials and guides
- **Build System**: PyInstaller configuration and Windows installer

#### 5. Before Submitting
- [ ] Code follows Python PEP 8 standards
- [ ] All tests pass locally
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] Windows compatibility verified

For detailed development guidelines, see [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

### Documentation

Comprehensive documentation is available in the `/docs` folder:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and component overview
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development setup and maintenance guide
- **[API.md](docs/API.md)** - LiteLLM integration and API documentation
- **[PRD.md](docs/PRD.md)** - Product requirements and specifications

## 🎯 Performance

WindVoice is optimized for minimal resource usage:

- **Memory Usage**: <50MB baseline
- **Startup Time**: <2 seconds to ready state
- **Recording Latency**: <100ms from hotkey to recording start
- **Background CPU**: <1% when idle

## 🔒 Security

- **Credential Storage**: Configuration stored in user home directory
- **API Security**: HTTPS-only communication with certificate validation
- **No Logging**: API keys and sensitive data never logged
- **Local Processing**: Audio validation performed locally before API calls

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 🎤 Audio Issues

**Problem: Audio not recording**

*Symptoms:* No response when pressing hotkey, "No voice detected" messages

*Diagnostic:*
```bash
# List available audio devices
python -c "
from windvoice.services.audio import AudioRecorder
recorder = AudioRecorder()
devices = recorder.list_audio_devices()
for i, device in enumerate(devices):
    print(f'{i}: {device}')
"
```

*Solutions:*
- Check microphone permissions in Windows Settings → Privacy → Microphone
- Update audio drivers
- Try different audio devices in Settings
- Run as administrator if using external audio interfaces

**Problem: "Microphone is being used by another application"**
- Close other applications using the microphone (video calls, recording software)
- Restart WindVoice after closing conflicting applications

#### 🔌 LiteLLM Connection Issues

**Problem: API connection failures**

*Symptoms:* "Transcription failed" errors, connection timeout messages

*Diagnostic:*
```bash
# Test API configuration
python -c "
import asyncio
from windvoice.core.config import ConfigManager
from windvoice.services.transcription import TranscriptionService

async def test():
    config = ConfigManager().load_config()
    service = TranscriptionService(config.litellm)
    success, message = await service.test_connection()
    print(f'Connection: {'✅' if success else '❌'} {message}')

asyncio.run(test())
"
```

*Solutions:*
- Verify API credentials in Settings
- Check network connectivity
- Confirm LiteLLM proxy URL is accessible
- Contact Thomson Reuters support for credential issues

#### ⌨️ Hotkey Issues

**Problem: Global hotkey not working**

*Symptoms:* No response when pressing `Ctrl+Shift+Space`

*Solutions:*
- Check for conflicting applications using the same hotkey
- Try alternative hotkey combinations in Settings
- Run WindVoice as administrator
- Restart Windows (for persistent hotkey conflicts)

#### 🔧 Performance Issues

**Problem: High memory usage**

*Solutions:*
- Restart the application periodically
- Check for audio buffer leaks (see logs)
- Ensure proper cleanup after transcription

**Problem: Slow transcription**

*Solutions:*
- Check network connectivity to LiteLLM proxy
- Verify audio quality (clear speech, minimal background noise)
- Try shorter recording sessions

#### 📁 Configuration Issues

**Problem: Settings not saving**

*Solutions:*
- Check file permissions for `%USERPROFILE%\.windvoice\config.toml`
- Run as administrator if needed
- Manually edit configuration file as backup

### Getting Help

If you encounter issues not covered here:

1. **Enable debug logging:**
   ```bash
   set WINDVOICE_LOG_LEVEL=DEBUG
   python main.py
   ```

2. **Check logs:** Look for detailed error information in the console output

3. **Report issues:** Create an issue on the repository with:
   - Steps to reproduce
   - Error messages or log excerpts (remove sensitive data)
   - Windows version and Python version
   - Configuration details (without API keys)

## 🚧 Current Status

**✅ Completed (Sprint 2)**
- ✅ Core audio recording and validation system
- ✅ LiteLLM transcription integration with retry logic
- ✅ Smart text injection with fallback popups
- ✅ Global hotkey management
- ✅ System tray integration with visual feedback
- ✅ Advanced audio validation and quality scoring
- ✅ Real-time recording level monitoring
- ✅ Comprehensive error handling and user notifications
- ✅ Settings interface with live validation
- ✅ Multiple status dialog implementations

**🔄 In Progress (Sprint 3)**
- 🔄 Test suite implementation
- 🔄 Performance optimization
- 🔄 Build and distribution system

**📋 Planned (Future)**
- 📋 PyInstaller executable builds
- 📋 Windows installer creation
- 📋 Performance benchmarking
- 📋 Production release preparation

## 🤝 Contributing

We welcome contributions from developers, testers, and documentation writers! See the [Contributing](#contributing) section in the Development guide above for detailed information.

Quick start for contributors:
1. Review the [Development Guide](docs/DEVELOPMENT.md) for detailed setup
2. Check the [Architecture Documentation](docs/ARCHITECTURE.md) to understand the system
3. Look at current issues or suggest new features
4. Follow the code standards and testing requirements

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Thomson Reuters for LiteLLM proxy integration
- OpenAI for Whisper speech recognition model
- The Python community for excellent libraries and tools

---

**Made with ❤️ for Windows users who want fast, accurate voice dictation**
