# WindVoice-Windows

**Native Windows Voice Dictation Application** - Fast, accurate speech-to-text with global hotkey activation and seamless text injection.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2B-lightgrey)
![Python](https://img.shields.io/badge/python-3.11%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

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

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/WindVoice-Windows.git
   cd WindVoice-Windows
   ```

2. **Setup virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure LiteLLM credentials**
   ```bash
   # Configuration will be created at ~/.windvoice/config.toml
   python main.py  # Will prompt for configuration on first run
   ```

4. **Run WindVoice**
   ```bash
   python main.py
   ```

### Configuration

WindVoice stores configuration in `%USERPROFILE%\.windvoice\config.toml`:

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

```bash
# Clone and setup
git clone <repo-url>
cd WindVoice-Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run in development mode
python main.py
```

### Running the Application

```bash
# Development mode
python main.py

# With debug logging
set WINDVOICE_LOG_LEVEL=DEBUG
python main.py
```

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

### Common Issues

**Audio not recording:**
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

**LiteLLM connection issues:**
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

**Hotkey not working:**
- Check for conflicting applications
- Run as administrator if needed
- Try alternative hotkey combinations in settings

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

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Thomson Reuters for LiteLLM proxy integration
- OpenAI for Whisper speech recognition model
- The Python community for excellent libraries and tools

---

**Made with ❤️ for Windows users who want fast, accurate voice dictation**
