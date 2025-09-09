# WindVoice-Windows

**Native Windows Voice Dictation Application** - Fast, accurate speech-to-text with global hotkey activation and seamless text injection.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2B-lightgrey)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🎤 Overview

WindVoice-Windows is a **100% Python** voice dictation application designed for Windows 10+ systems. It provides instant voice recording with global hotkey activation (`Ctrl+Shift+Space`) and smart text injection into any Windows application.

## ✨ Key Features

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
- Python 3.10+ (recommended: Python 3.11 or 3.12)
- Thomson Reuters LiteLLM API credentials

### Installation

Choose your preferred installation method:

#### Option 1: Portable Executable (Recommended)

1. **Download or Build EXE**
   ```bash
   # Build portable executable
   pyinstaller WindVoice.spec --clean --noconfirm
   ```

2. **Run**
   - Navigate to `dist/` folder
   - Double-click `WindVoice-Windows.exe`
   - No installation required - runs immediately

> **Why EXE is recommended:** Due to organizational permission policies, MSI installers may install successfully but cannot be uninstalled without admin privileges, potentially leaving the system in a blocked state.

#### Option 2: MSI Installer (Alternative)

1. **Download or Build MSI**
   ```bash
   # Build MSI installer
   python build.py
   ```

2. **Install**
   - Double-click `installer/WindVoice-Windows-Installer.msi`
   - Follow installation wizard
   - Launch from Start Menu

> **Note:** MSI installation may require admin privileges for uninstallation. Use only if you have full admin access or prefer system integration.

#### Option 3: Python Development

```bash
# Clone and setup
git clone <repository-url>
cd WindVoice-Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Configuration

On first run, configure via the setup wizard or manually edit `%USERPROFILE%\.windvoice\config.toml`:

```toml
[litellm]
api_key = "sk-your-litellm-api-key"
api_base = "https://your-litellm-proxy.com"
key_alias = "your-username"
model = "whisper-1"
```

See the [Installation Guide](docs/INSTALLER_GUIDE.md) for detailed setup instructions.

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

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[Installation Guide](docs/INSTALLER_GUIDE.md)** - Complete installation and setup instructions
- **[Development Guide](docs/DEVELOPMENT.md)** - Development setup, coding standards, and contribution guidelines
- **[Architecture Documentation](docs/ARCHITECTURE.md)** - System design and technical architecture details
- **[API Documentation](docs/API.md)** - LiteLLM integration and API reference
- **[Product Requirements](docs/PRD.md)** - Product specifications and implementation status

## 🤝 Contributing

We welcome contributions! Quick start:

1. Fork the repository
2. Review the [Development Guide](docs/DEVELOPMENT.md) for setup instructions
3. Check the [Architecture Documentation](docs/ARCHITECTURE.md) to understand the system
4. Follow coding standards and submit a Pull Request

**Areas for contribution:**
- Testing and test suite implementation
- Performance optimization
- UI/UX enhancements
- Documentation improvements

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Thomson Reuters for LiteLLM proxy integration
- OpenAI for Whisper speech recognition model
- The Python community for excellent libraries and tools

---

**Made with ❤️ for Windows users who want fast, accurate voice dictation**
