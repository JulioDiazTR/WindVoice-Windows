# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WindVoice is a modern cross-platform voice dictation application that enables fast and accurate audio-to-text transcription with automatic text insertion into any active application. This repository contains the Windows Python implementation of WindVoice, designed as a complete rewrite from the previous Electron version for improved performance and resource efficiency.

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
├── core/               # Application controller, state management, config
├── services/           # Audio, hotkeys, text injection, transcription, tray
├── ui/                # CustomTkinter interface, popup dialogs, settings
└── utils/             # Cross-platform helpers, file management, logging
```

## Development Commands

Since this is an early-stage project without implemented build system yet:

### Project Setup
```bash
# Install dependencies (when requirements.txt exists)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run application entry point
python main.py
```

### Testing
```bash
# Run test suite (when implemented)
pytest tests/
pytest tests/unit/          # Unit tests only  
pytest tests/integration/   # Integration tests only
python scripts/test.py      # Test runner with coverage
```

### Build and Distribution
```bash
# Build executable (when implemented)
python scripts/build.py    # PyInstaller build script
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
- Direct aiohttp POST calls to `/v1/audio/transcriptions` endpoint
- Simple retry logic (3 attempts with 1-second delays)
- High-quality WAV audio format (44.1kHz, 16-bit) optimized for Whisper
- User-friendly error handling with clear, non-technical messages

## Core User Workflows

### Primary: Global Hotkey Mode (80% usage)
1. User presses `Ctrl+Shift+Space` from any application
2. Instant recording begins with pre-initialized audio stream
3. Second hotkey press stops recording  
4. Automatic transcription via LiteLLM
5. Smart text handling: auto-inject if text field detected, otherwise show popup

### Secondary: Manual UI Mode (20% usage)
1. User opens WindVoice from system tray
2. Manual recording controls with visual feedback
3. Transcription review and editing capabilities
4. Flexible actions: copy, inject, or save results

## Smart UI Decision Logic

The application uses intelligent context-aware behavior:
- **Auto-injection preferred:** Direct text insertion when active text field detected
- **Smart popup fallback:** Always-on-top dialog when no injection target
- **UI coordination:** Seamless switching between main window, popup, and background modes

## Performance Targets

- **Memory Usage:** <50MB baseline (3x improvement over Electron)
- **Startup Time:** <2 seconds from launch to ready
- **Recording Latency:** <100ms from hotkey press to recording start
- **Text Injection:** <200ms from transcription complete to text appearance
- **Background CPU:** <1% when idle

## Security Requirements

- Never hardcode API keys or credentials in source code
- Store sensitive configuration in user's home directory (`~/.windvoice/config.toml`)
- Never log API keys or sensitive data - only log configuration status
- Use system's secure storage mechanisms when available
- Provide user-friendly error messages without exposing technical details

## Development Phases

The project follows a sprint-based development approach:

1. **Sprint 1:** Foundation & Core Audio (recording + transcription)
2. **Sprint 2:** Modern UI & Manual Controls  
3. **Sprint 3:** Global Hotkeys & Background Operation
4. **Sprint 4:** Smart Text Injection & UI Logic
5. **Sprint 5:** Polish & Distribution

## Cross-Platform Considerations

- **Windows 10+** and **macOS 12+** support required
- Use platform-specific optimizations for text injection reliability
- Handle audio device differences across operating systems
- Consistent behavior and UI appearance across platforms

## Error Handling Philosophy

- Show clear, user-friendly error messages
- Avoid technical jargon in user-facing messages
- Example: "Transcription service is temporarily unavailable" vs "HTTPConnectionError: 503"
- Fail gracefully without crashing
- Provide actionable guidance when possible
- All code must be properly commented.
- All generated code must be in English.
- All code must be documented in English
- Python best practices should always be used
- Every key should not be commented or hardcoded in the code, env should be used for handling sensitive data that should not go in the repo
- You should always review the docs folder to understand how the app works and the app specifications before making any changes to the app.
- After making changes, the documentation should always be updated.
- All documentation created must be in English.
- All code created must be testable
- For new features and developments, associated testing development must be done.