# PRD - WindVoice-Windows: Native Windows Voice Dictation App

## 📋 Product Overview

**Product Name:** WindVoice-Windows  
**Version:** 2.0.0  
**Platform:** Windows 10+  
**Tech Stack:** 100% Python (CustomTkinter + Modern Audio Stack)  
**Target Release:** Q4 2025  

### Vision Statement
Create a **simple, fast, and reliable** Windows voice dictation application using 100% Python. Focus on system tray presence with global hotkey activation that works seamlessly across any Windows application.

### Design Principles
- 🎯 **Simple**: Easy to use, understand, and maintain
- 🔒 **Secure**: Safe handling of API keys and user data
- 👤 **Usable**: Intuitive interface with clear feedback
- ⚡ **Fast**: Instant response with minimal overhead
- 🛡️ **Reliable**: Works consistently, shows errors clearly when they occur

### Key Features
- ⚡ **Instant hotkey activation** from any application (Ctrl+Shift+Space)
- 🎤 **High-quality audio recording** (44.1kHz WAV optimized for Whisper)
- 🤖 **AI transcription** using Thomson Reuters LiteLLM proxy with Whisper-1
- 💉 **Smart text injection** - auto-inject or minimal popup based on context
- 🖲️ **System tray presence** - lives quietly in Windows system tray
- ⚙️ **Minimal configuration** - API keys and essential preferences only
- 🔒 **Privacy-focused** - secure credential handling
- 📝 **Clear error handling** - user-friendly messages without technical details

---

## 🏗️ Architecture & Technical Specifications

### System Architecture - Unified Python Process

```
┌─────────────────────────────────────────────────────────────┐
│                  WindVoice Python App                      │
│                    (Single Process)                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              UI Layer (CustomTkinter)                   │ │
│  │  ┌──────────────┬────────────────┬──────────────────┐  │ │
│  │  │ Main Window  │ Settings Panel │ Transcription    │  │ │
│  │  │ (Optional)   │               │ Popup Dialog     │  │ │
│  │  └──────────────┴────────────────┴──────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   Services Layer                        │ │
│  │  ┌──────────────┬────────────────┬──────────────────┐  │ │
│  │  │ Audio        │ Hotkey         │ Text Injection   │  │ │
│  │  │ Recorder     │ Manager        │ Service          │  │ │
│  │  └──────────────┴────────────────┴──────────────────┘  │ │
│  │  ┌──────────────┬────────────────┬──────────────────┐  │ │
│  │  │ Transcription│ System Tray    │ State Manager    │  │ │
│  │  │ Service      │ Service        │ (Thread-Safe)    │  │ │
│  │  └──────────────┴────────────────┴──────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Core Layer                              │ │
│  │  • Application Controller                               │ │
│  │  • Configuration Management                             │ │
│  │  • Windows-Specific Utilities                        │ │
│  │  • File System Management                              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS API Calls
                              ▼
      ┌─────────────────────────────────────────┐
      │     Thomson Reuters LiteLLM Proxy       │
      │         (External Service)              │
      │  • OpenAI Whisper-1 Model              │
      │  • Requires: LITELLM_API_KEY           │
      │  • Requires: LITELLM_API_BASE          │
      │  • Requires: KEY_ALIAS                 │
      │  • Model: "whisper-1"                  │
      └─────────────────────────────────────────┘
```

### Technology Stack - 100% Python

#### Core Framework
- **UI Framework:** CustomTkinter 5.2.2+ (Modern, beautiful native UI)
- **Audio Processing:** sounddevice 0.4.7 + soundfile 0.12.1 + numpy
- **System Integration:** pynput 1.7.7 (hotkeys + text injection)
- **Background Services:** pystray 0.19.4 (system tray)
- **Async Operations:** asyncio + aiohttp 3.9.1

#### Configuration & Security
- **LiteLLM Integration:** Direct aiohttp calls to Thomson Reuters proxy
  - **Required Environment Variables:**
    - `LITELLM_API_KEY` - Virtual API key from Thomson Reuters
    - `LITELLM_API_BASE` - Proxy URL (e.g., https://your-proxy.com)
    - `KEY_ALIAS` - User identifier for usage tracking
  - **Model:** `whisper-1` (OpenAI Whisper via proxy)
  - **Security:** Never hardcode credentials, always use config files
- **Configuration:** Simple TOML config with user settings directory
- **Error Handling:** Simple, clear error messages for users
- **Testing:** Basic pytest for core functionality only

#### Native Python Benefits
- **Lightweight:** ~30-50MB memory footprint
- **Fast startup:** 1-2 second application launch
- **Single ecosystem:** Pure Python development and maintenance
- **Native performance:** Direct Windows OS integration without web layer overhead
- **Windows-optimized:** Tailored for Windows 10+ environment

### Project Structure

```
WindVoice-Windows/
├── src/
│   ├── windvoice/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── app.py                    # Main application controller
│   │   │   ├── config.py                 # Configuration management  
│   │   │   └── exceptions.py             # Custom exception classes
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── audio.py                  # Audio recording and validation service
│   │   │   ├── hotkeys.py                # Global hotkey handling
│   │   │   ├── injection.py              # Windows text injection service
│   │   │   └── transcription.py          # LiteLLM integration with validation
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── menubar.py                # System tray/menu bar presence
│   │   │   ├── popup.py                  # Minimal transcription popup
│   │   │   └── settings.py               # Configuration panel
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── windows.py                # Windows-specific helpers
│   │       ├── audio_validation.py       # Audio quality and silence detection
│   │       └── logging.py                # Logging configuration
# Test structure (planned for Sprint 3):
# ├── tests/
# │   ├── unit/                           # Unit tests for individual components  
# │   ├── integration/                    # Integration workflow tests
# │   ├── performance/                    # Performance and memory tests
# │   └── fixtures/                       # Test data and mock resources
# Additional directories (planned):
# ├── config/                           # Configuration templates
# ├── assets/                           # Icons and audio files
# └── dist/                             # Built executables
├── docs/
│   ├── README.md                         # Project overview and quick start
│   ├── DEVELOPMENT.md                    # Development setup guide
│   └── ARCHITECTURE.md                   # Technical architecture details
├── requirements.txt                      # Production dependencies
├── main.py                              # Application entry point
├── run_windvoice.py                     # Alternative entry point
└── .gitignore                           # Git ignore rules

# Future additions (planned for Sprint 3):
# ├── scripts/                           # Build and utility scripts
# ├── requirements-dev.txt               # Development dependencies
# ├── pyproject.toml                     # Modern Python project configuration
# └── config.example.toml                # Configuration template
```

---

## 🚀 User Experience & Workflows

### Primary Use Case: System Tray Mode (90% of usage)

**Background Operation:**
1. **App Launch**: WindVoice lives quietly in system tray/menu bar
2. **Hotkey Activation**: User presses `Ctrl+Shift+Space` from **any application**
3. **Instant Recording**: Recording begins immediately with minimal visual feedback
4. **Stop Recording**: Second hotkey press or automatic silence detection stops recording
5. **Audio Validation**: Check for empty audio or silence before transcription
6. **Smart Processing**: 
   - **Valid audio detected** → Send to LiteLLM for transcription
   - **Empty/silent audio** → Show notification "No voice detected in recording"
7. **Smart Text Handling**: 
   - **Successful transcription + Active text field** → Auto-inject text immediately
   - **Successful transcription + No active field** → Show popup with transcription
   - **Failed/empty transcription** → Clear user notification
8. **Return to Background**: App remains invisible, user continues working

### Secondary Use Case: Settings Access (10% of usage)

**Minimal Configuration Interface:**
1. **Settings Access**: Right-click system tray icon → Settings
2. **API Configuration**: Set LiteLLM credentials and preferences
3. **Hotkey Customization**: Configure activation shortcuts
4. **Audio Preferences**: Device selection, quality settings, and silence detection
5. **Smart Notifications**: Configure empty audio detection alerts

### Smart UI Decision Logic

**Intelligent Context-Aware Behavior:**
```python
async def handle_audio_processing(self, audio_file_path: str):
    """Smart audio processing with validation"""
    
    # 1. Validate audio content before transcription
    audio_validation = self.validate_audio_content(audio_file_path)
    if not audio_validation.has_voice:
        self.show_user_notification(
            "No voice detected in recording", 
            "Please try recording again and speak clearly."
        )
        return
    
    # 2. Proceed with transcription
    try:
        text = await self.transcribe_audio(audio_file_path)
        if text.strip():
            await self.handle_transcription_result(text)
        else:
            self.show_user_notification(
                "Transcription returned empty",
                "Audio was processed but no text was generated."
            )
    except Exception as e:
        self.show_user_notification(
            "Transcription failed",
            "Please check your internet connection and try again."
        )

async def handle_transcription_result(self, text: str):
    """Handle successful transcription results"""
    
    # Try auto-injection (preferred method)
    if self.detect_active_text_field():
        success = await self.inject_text_safely(text)
        if success:
            self.show_brief_confirmation("✅ Text injected")
            return
    
    # Fallback to popup
    popup = SmartTranscriptionPopup(text)
    popup.show_with_focus()
```

**Smart Popup Features:**
- **Small, focused window** with transcription text or status message
- **Quick actions**: Copy (Ctrl+C), Paste to active app (Enter), Dismiss (Escape)
- **Auto-positioning** near cursor or screen center
- **Auto-dismiss** after action or 10-second timeout
- **Smart notifications**: Clear feedback for empty audio or recording issues
- **Keyboard-first** interaction for Windows users

---

## 📊 Development Plan & Milestones

### Sprint Structure (1-2 weeks per sprint)

## Sprint 1: Minimal Viable Product (SuperWhisper-inspired) 🎤

### Epic 1.1: Core Foundation
| Task | Description | Est. Hours | Priority |
|------|-------------|------------|----------|
| Project Structure | Simple Python package structure | 2h | Critical |
| Configuration System | Basic TOML config for API credentials | 2h | Critical |
| System Tray Setup | pystray menu bar presence | 3h | Critical |
| Global Hotkeys | pynput hotkey registration (Ctrl+Shift+Space) | 3h | Critical |
| **Total Sprint 1.1** | **Basic app foundation** | **10h** | |

### Epic 1.2: Audio → Text Pipeline
| Task | Description | Est. Hours | Priority |
|------|-------------|------------|----------|
| Audio Recording | sounddevice implementation with start/stop | 4h | Critical |
| WAV File Export | High-quality 44.1kHz output for Whisper | 2h | Critical |
| Audio Validation | Detect empty/silent audio before transcription | 3h | Critical |
| LiteLLM Integration | Direct aiohttp POST to transcription endpoint | 4h | Critical |
| Smart Error Handling | Retry logic and clear user notifications for empty audio | 3h | High |
| **Total Sprint 1.2** | **Working transcription pipeline with validation** | **16h** | |

### Epic 1.3: Smart Text Injection
| Task | Description | Est. Hours | Priority |
|------|-------------|------------|----------|
| Text Injection Service | pynput keyboard automation | 3h | Critical |
| Active Field Detection | Basic detection of text input fields | 3h | High |
| Minimal Popup | Simple popup for when injection fails | 3h | High |
| Integration Testing | End-to-end workflow validation | 2h | Critical |
| **Total Sprint 1.3** | **Complete minimal workflow** | **11h** | |

**LiteLLM Integration Details:**
```python
# Simple direct integration - no over-engineering
async def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio using Thomson Reuters LiteLLM proxy"""
    url = f"{config.litellm_api_base}/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {config.litellm_api_key}",
        "X-Key-Alias": config.key_alias
    }
    data = aiohttp.FormData()
    data.add_field('file', open(audio_file_path, 'rb'), filename='audio.wav')
    data.add_field('model', 'whisper-1')
    
    # Simple retry logic - 3 attempts max
    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['text']
                    else:
                        error_text = await response.text()
                        raise Exception(f"API Error {response.status}: {error_text}")
        except Exception as e:
            if attempt == 2:  # Last attempt
                raise Exception(f"Transcription failed after 3 attempts: {str(e)}")
            await asyncio.sleep(1)  # Wait 1 second before retry
```

**Sprint 1 Deliverable**: Complete hotkey → record → transcribe → inject workflow working

---

## Sprint 2: Polish & Settings ⚙️

### Epic 2.1: Settings Interface
| Task | Description | Est. Hours | Priority |
|------|-------------|------------|----------|
| Settings Window | Simple dialog for configuration | 3h | Critical |
| API Configuration | Form for LiteLLM credentials (API_KEY, API_BASE, KEY_ALIAS) | 2h | Critical |
| Hotkey Customization | Allow users to change activation hotkey | 3h | High |
| Audio Device Selection | Dropdown for microphone selection | 2h | High |
| Settings Persistence | Save/load config from TOML file | 2h | Critical |
| **Total Sprint 2.1** | **Complete settings management** | **12h** | |

### Epic 2.2: Enhanced User Experience
| Task | Description | Est. Hours | Priority |
|------|-------------|------------|----------|
| Visual Feedback | Tray icon animation during recording | 2h | High |
| Audio Quality Indicators | Show recording levels and silence detection | 3h | High |
| Smart Notifications | Clear messages for empty audio, transcription status | 3h | Critical |
| Empty Audio Alerts | User-friendly notifications when no voice detected | 2h | Critical |
| Keyboard Shortcuts | Quick actions in popup (Enter, Escape, Ctrl+C) | 2h | High |
| **Total Sprint 2.2** | **Polished user experience with smart feedback** | **12h** | |

**Sprint 2 Deliverable**: Production-ready application with full configuration capabilities

---

## Sprint 3: Distribution & Final Polish 🚀

### Epic 3.1: Build & Packaging
| Task | Description | Est. Hours | Priority |
|------|-------------|------------|----------|
| PyInstaller Setup | Single executable build configuration | 4h | Critical |
| Icon & Assets | Proper icon integration and asset bundling | 2h | High |
| Windows Testing | Comprehensive testing on Windows 10+ systems | 4h | Critical |
| Installation Process | Simple installer or portable executable | 3h | High |
| **Total Sprint 3.1** | **Distributable application** | **13h** | |

### Epic 3.2: Final Testing & Optimization
| Task | Description | Est. Hours | Priority |
|------|-------------|------------|----------|
| Performance Optimization | Memory usage and startup time optimization | 4h | High |
| Comprehensive Testing | End-to-end workflow validation | 4h | Critical |
| Error Handling Review | Ensure all error scenarios are handled gracefully | 3h | High |
| Documentation | User guide and troubleshooting documentation | 3h | Medium |
| **Total Sprint 3.2** | **Production-ready quality** | **14h** | |

**Sprint 3 Deliverable**: Production-ready WindVoice application ready for distribution

---

## 🎯 Success Criteria & Technical Requirements

### Functional Requirements
- ✅ **Global hotkey activation** works from any application (Ctrl+Shift+Space)
- ✅ **Instant recording start** with pre-initialized audio system (<100ms delay)
- ✅ **High-quality audio capture** (44.1kHz, 16-bit WAV, optimized for Whisper)
- ✅ **Reliable transcription** using existing LiteLLM Thomson Reuters integration
- ✅ **Smart text injection** with 95%+ success rate across applications
- ✅ **Context-aware UI** - auto-injection vs popup based on active text fields
- ✅ **Background operation** with minimal system tray footprint
- ✅ **Windows compatibility** optimized for Windows 10+ environment

### Performance Requirements
- 🚀 **Memory Usage**: <50MB baseline (lightweight native app)
- ⚡ **Startup Time**: <2 seconds from launch to ready
- 🎤 **Recording Latency**: <100ms from hotkey press to recording start
- 🤖 **Transcription Speed**: <3 seconds for typical 10-second audio clip
- 💉 **Text Injection**: <200ms from transcription complete to text appear
- 🔄 **Background CPU**: <1% when idle (minimal system impact)

### Quality Requirements (Simple & Practical)
- 🧪 **Testing**: Basic tests for core functions only - no over-testing
- 🛡️ **Error Handling**: Show clear error messages to users, don't crash
- 🔒 **Security**: 
  - Store API keys in user config file (not hardcoded)
  - Never log API keys or sensitive data
  - Use system's secure storage when available
- 📊 **Reliability**: App should work consistently, handle common errors gracefully
- 🎧 **Audio Validation**: Detect and report empty or silent recordings
- 📝 **Error Messages**: User-friendly, not technical
  - ❌ "HTTPConnectionError: 503 Service Unavailable"
  - ✅ "Transcription service is temporarily unavailable. Try again in a moment."

### User Experience Requirements
- 📱 **Intuitive UI**: Users can accomplish core tasks without documentation
- 🚀 **Responsive Feedback**: Visual feedback for all actions within 100ms
- 🎯 **Smart Behavior**: App makes correct decisions about injection vs popup 95% of time
- 🔧 **Customizable**: Hotkeys, settings, and behavior configurable by user
- 📞 **Accessibility**: Keyboard shortcuts and screen reader friendly

---

## ⚙️ Configuration & LiteLLM Setup

### Configuration File (config.toml)
```toml
[litellm]
# Thomson Reuters LiteLLM Proxy Configuration
# REQUIRED: Get these values from your Thomson Reuters admin
api_key = ""           # Your virtual API key (sk-xxxxx)
api_base = ""          # Proxy URL (https://your-proxy.com)
key_alias = ""         # Your user identifier
model = "whisper-1"    # OpenAI Whisper model via proxy

[app]
# Application Settings
hotkey = "ctrl+shift+space"    # Global hotkey combination
audio_device = "default"       # Audio input device
sample_rate = 44100            # Audio sample rate (optimized for Whisper)

[ui]
# User Interface Settings  
theme = "dark"                 # UI theme (dark/light)
window_position = "center"     # Window position on startup
show_tray_notifications = true # Show system tray notifications
```

### Environment Variables (Alternative)
```bash
# Alternative to config.toml - use environment variables
export LITELLM_API_KEY="sk-your-key-here"
export LITELLM_API_BASE="https://your-proxy.com"
export KEY_ALIAS="your-username"
```

### Security Best Practices
- **Never hardcode** API keys in source code
- **Use config file** in user's home directory (`~/.windvoice/config.toml`)
- **Validate configuration** on startup - show clear error if missing
- **No logging** of API keys, only log "API key configured: Yes/No"

### Error Handling Examples
```python
# Audio validation and user-friendly error messages
def validate_audio_content(audio_file_path: str) -> AudioValidation:
    """Validate audio contains speech before transcription"""
    audio_data, sample_rate = sf.read(audio_file_path)
    
    # Check for silence (RMS below threshold)
    rms = np.sqrt(np.mean(audio_data**2))
    silence_threshold = 0.01  # Adjustable threshold
    
    # Check duration
    duration = len(audio_data) / sample_rate
    min_duration = 0.5  # Minimum 0.5 seconds
    
    return AudioValidation(
        has_voice=rms > silence_threshold and duration >= min_duration,
        rms_level=rms,
        duration=duration
    )

# User-friendly error handling
if not config.litellm_api_key:
    show_error("LiteLLM API key not configured. Please check Settings.")
    return

if not audio_validation.has_voice:
    show_notification(
        "No voice detected",
        "Your recording appears to be silent. Please try again."
    )
elif response.status == 401:
    show_error("API key is invalid. Please check your LiteLLM settings.")
elif response.status == 503:
    show_error("Transcription service is temporarily unavailable.")
else:
    show_error(f"Transcription failed. Please try again.")
```

## 🚀 Implementation Benefits

### Native Python Advantages
| Aspect | Target | Benefit |
|--------|--------|----------|
| **App Size** | ~35MB installer | Compact distribution |
| **Memory Usage** | ~45MB runtime | Lightweight operation |
| **Startup Time** | 1-2 seconds | Fast application launch |
| **Text Injection Reliability** | 98% success rate | Cross-app compatibility |
| **Development Complexity** | Single Python codebase | Simplified maintenance |
| **Native Integration** | Direct OS APIs | Superior performance |

---

## 📈 Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Windows Audio Device Compatibility
- **Risk**: sounddevice driver issues on different Windows systems
- **Mitigation**: 
  - Multiple fallback audio libraries (pyaudio, wave)
  - Comprehensive Windows audio device compatibility testing
  - Clear error messages and audio device selection UI
  - Windows-specific audio API optimization

#### Medium Risk: Text Injection Reliability  
- **Risk**: Different applications handle pynput injection differently
- **Mitigation**:
  - Multiple injection methods (direct typing, clipboard+paste)
  - Application-specific injection profiles
  - Extensive testing matrix across popular applications

#### Medium Risk: Global Hotkey Conflicts
- **Risk**: Hotkey conflicts with other applications
- **Mitigation**:
  - Customizable hotkey configuration
  - Conflict detection and alternative suggestions
  - Multiple hotkey options (Ctrl+Alt+Space, Ctrl+Shift+V, etc.)

### Project Risks

#### Low Risk: CustomTkinter UI Limitations
- **Risk**: CustomTkinter may not support all desired UI features
- **Mitigation**:
  - Flet as alternative modern Python UI framework
  - Focus on functional UI over complex visual effects
  - Progressive enhancement approach

#### Low Risk: PyInstaller Distribution Issues
- **Risk**: Single executable may have compatibility issues
- **Mitigation**:
  - Alternative: cx_Freeze or Nuitka for packaging
  - Virtual environment distribution as fallback
  - Comprehensive testing on clean systems

---

## 🏆 Success Metrics & KPIs

### Development Metrics
- **Code Quality**: >90% test coverage, <10 critical bugs
- **Development Speed**: Core functionality complete in 6 weeks
- **Technical Debt**: <20% of time spent on refactoring vs new features

### Performance Metrics  
- **Resource Usage**: <50MB memory, <1% idle CPU
- **Responsiveness**: <100ms UI response time, <3s transcription
- **Reliability**: <1 crash per 100 hours of usage

### User Experience Metrics
- **Success Rate**: >95% of recordings result in successful text injection or user action
- **User Satisfaction**: >8/10 user satisfaction score
- **Reliability**: <1 failure per 100 transcription attempts

---

**Document Version**: 1.0  
**Created**: 2025-01-09  
**Target Audience**: Development team and stakeholders  
**Next Review**: After Sprint 2 completion  
**Status**: Ready for development - comprehensive Python-only architecture defined

**Key Success Factor**: SuperWhisper-inspired simplicity - menu bar presence, instant hotkey activation, and seamless text injection with minimal user interface complexity.