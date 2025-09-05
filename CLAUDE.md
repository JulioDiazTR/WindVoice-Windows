# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WindVoice-Windows is a native Windows voice dictation application that enables fast and accurate audio-to-text transcription with automatic text insertion into any Windows application. Built with 100% Python for optimal performance and resource efficiency on Windows 10+ systems.

## Architecture

The project follows a **100% Python architecture** using a single unified process design:

- **UI Framework:** CustomTkinter 5.2.2+ for modern, beautiful native UI
- **Audio Processing:** sounddevice + soundfile + numpy for high-quality recording
- **System Integration:** pynput for global hotkeys and text injection
- **Background Services:** pystray for system tray management
- **Async Operations:** asyncio + aiohttp for LiteLLM integration
- **Configuration:** TOML-based configuration system

## Key Components Structure

```
src/windvoice/
├── core/               # Application controller, config, exceptions
├── services/           # Audio recording/validation, hotkeys, text injection, transcription
├── ui/                # System tray, popup dialog, settings panel
└── utils/             # Windows-specific helpers, audio validation, logging
```

## Development Commands

### Project Setup
```bash
# Development installation (recommended for development)
pip install -e .

# Or install dependencies separately
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools

# Run application entry point
python main.py

# Or use the installed script (after pip install -e .)
windvoice
```

### Testing
```bash
# Run test suite (when implemented)
pytest tests/
pytest tests/unit/          # Unit tests only  
pytest tests/integration/   # Integration tests only
pytest --cov=windvoice      # With coverage
```

### Build and Distribution
```bash
# RECOMMENDED: Build MSI installer (professional Windows installation)
python build.py

# Alternative: Install WiX Toolset first (if not installed)
python install_wix.py

# Build wheel for distribution (may fail on Python 3.13)
python -m build

# Manual PyInstaller build (creates portable .exe only)
pyinstaller WindVoice.spec --clean --noconfirm

# Install from built wheel (if build succeeds)
pip install dist/windvoice_windows-1.0.0-py3-none-any.whl
```

### Installation for End Users
```bash
# RECOMMENDED: Install from MSI installer (creates Start Menu shortcuts, auto-start, proper uninstall)
# 1. Run: python build.py
# 2. Double-click: installer/WindVoice-Windows-Installer.msi

# Alternative: Install from source (development/testing)
pip install .

# Install with development tools
pip install .[dev]

# Install from PyPI (when published)
pip install windvoice-windows

# Emergency configuration tools (for troubleshooting)
WindVoice-Windows.exe --check-config    # Check configuration status
WindVoice-Windows.exe --create-config   # Create emergency configuration template
```

## Thomson Reuters LiteLLM Integration

This project integrates with Thomson Reuters' LiteLLM proxy for AI transcription using OpenAI's Whisper-1 model.

### Required Configuration
The application requires these configuration values in `config.toml`:

```toml
[litellm]
api_key = ""        # Virtual API key from Thomson Reuters (sk-xxxxx)
api_base = ""       # Proxy URL (https://your-proxy.com)  
key_alias = ""      # User identifier for usage tracking
model = "whisper-1" # OpenAI Whisper model via proxy
```

### Transcription Service Implementation
- **Audio validation first**: Check RMS levels and duration before API call
- Direct aiohttp POST calls to `/v1/audio/transcriptions` endpoint
- Simple retry logic (3 attempts with 1-second delays) 
- High-quality WAV audio format (44.1kHz, 16-bit) optimized for Whisper
- **Smart error handling**: 
  - Empty audio → "No voice detected" notification
  - API errors → User-friendly messages without technical details

## Core User Workflows

### Primary: System Tray Hotkey Mode (90% usage)
1. User presses `Ctrl+Shift+Space` from any Windows application
2. Instant recording begins with pre-initialized audio stream
3. Second hotkey press stops recording
4. **Audio validation**: Check for empty/silent audio before transcription
5. **Smart user feedback**: If no voice detected, show "No voice detected in recording"
6. **Transcription**: If valid audio, process via LiteLLM
7. **Smart injection**: Auto-inject if text field detected, otherwise show popup

### Secondary: Settings Access (10% usage)
1. Right-click system tray icon → Settings
2. Configure LiteLLM API credentials
3. Customize hotkeys and audio preferences
4. Set audio validation sensitivity

## Smart Audio Processing & UI Logic

### Audio Validation (Critical Feature)
- **Pre-transcription validation**: Check RMS levels and duration before sending to LiteLLM
- **Silent audio detection**: Notify user immediately if recording contains no voice
- **Configurable thresholds**: Adjustable sensitivity for silence detection
- **Clear notifications**: "No voice detected in recording. Please try again."

### Smart Text Handling
- **Auto-injection preferred**: Direct text insertion when active text field detected
- **Smart popup fallback**: Minimal popup when no injection target available
- **Windows-optimized**: Tailored for Windows text injection APIs

## Performance Targets

- **Memory Usage:** <50MB baseline (lightweight native Windows app)
- **Startup Time:** <2 seconds from launch to system tray ready
- **Recording Latency:** <100ms from hotkey press to recording start
- **Audio Validation:** <50ms to detect empty/silent audio
- **Text Injection:** <200ms from transcription complete to text appearance
- **Background CPU:** <1% when idle (minimal Windows system impact)

## Security Requirements

- Never hardcode API keys or credentials in source code
- Store sensitive configuration in user's home directory (`~/.windvoice/config.toml`)
- Never log API keys or sensitive data - only log configuration status
- Use system's secure storage mechanisms when available
- Provide user-friendly error messages without exposing technical details

## Development Phases

Simplified 3-sprint approach focused on Windows-native experience:

1. **Sprint 1:** MVP - Hotkey recording, audio validation, transcription, injection (33h)
2. **Sprint 2:** Settings UI, enhanced UX, smart notifications (24h)  
3. **Sprint 3:** Build system, distribution, final polish (27h)

## Windows-Specific Requirements

- **Windows 10+ compatibility** with modern Windows APIs
- **Native Windows integration** for reliable text injection
- **System tray behavior** following Windows UI guidelines
- **Windows audio system** optimization for device compatibility
- **Windows hotkey standards** and conflict resolution

## Development Standards

### Code Quality
- All code must be properly commented and documented in English
- Follow Python best practices and PEP 8 standards
- All code must be testable with associated unit tests
- Never hardcode sensitive data - use environment variables or config files

### Error Handling Philosophy
- **User-friendly messages**: "No voice detected in recording" vs technical errors
- **Smart notifications**: Clear feedback for empty audio, transcription failures
- **Graceful degradation**: Never crash, always provide actionable guidance
- **Examples**:
  - ✅ "Recording appears to be silent. Please try again."
  - ❌ "RMS threshold 0.01 not met in audio validation"

### Documentation Requirements
- Always review `docs/PRD.md` before making changes to understand specifications
- Update documentation after implementing features
- All documentation must be in English
- Include technical implementation details for audio validation and Windows integration

### Security Requirements
- Store LiteLLM credentials in `~/.windvoice/config.toml`
- Never log API keys or sensitive data
- Use Windows secure storage APIs when available