# PRD - WindVoice-Windows: Native Windows Voice Dictation App

## 📋 Product Overview

**Product Name:** WindVoice-Windows  
**Version:** 1.0.0 (MVP Complete)  
**Platform:** Windows 10+  
**Tech Stack:** 100% Python (CustomTkinter + Modern Audio Stack)  
**Current Status:** Implemented and Functional  

### Vision Statement
A **simple, fast, and reliable** Windows voice dictation application using 100% Python. Features system tray presence with global hotkey activation that works seamlessly across any Windows application.

### Design Principles
- 🎯 **Simple**: Easy to use, understand, and maintain
- 🔒 **Secure**: Safe handling of API keys and user data
- 👤 **Usable**: Intuitive interface with clear feedback
- ⚡ **Fast**: Instant response with minimal overhead
- 🛡️ **Reliable**: Works consistently, shows errors clearly when they occur

### Key Features (✅ IMPLEMENTED)
- ⚡ **Instant hotkey activation** from any application (Ctrl+Shift+Space)
- 🎤 **High-quality audio recording** (44.1kHz WAV optimized for Whisper)
- 🤖 **AI transcription** using Thomson Reuters LiteLLM proxy with Whisper-1
- 💉 **Smart text injection** - auto-inject with Windows text field detection
- 🖲️ **System tray presence** - lives quietly in Windows system tray
- ⚙️ **Settings interface** - CustomTkinter GUI for configuration
- 🎯 **Visual status feedback** - Non-focusable overlay showing recording/processing
- 🔍 **Audio validation** - Detects empty/silent audio before transcription
- 📝 **Smart popup fallback** - Shows text when injection fails
- 🔒 **Privacy-focused** - TOML config with secure credential handling

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

See the [Architecture Documentation](ARCHITECTURE.md) for detailed project structure and component organization.

---

## 🚀 User Experience & Workflows

### Primary Use Case: System Tray Mode (✅ IMPLEMENTED)

**Background Operation:**
1. **App Launch**: WindVoice lives quietly in system tray with pystray integration
2. **Hotkey Activation**: User presses `Ctrl+Shift+Space` from **any application** 
3. **Visual Feedback**: Non-focusable overlay shows "🎤 RECORDING" status
4. **Audio Recording**: High-quality 44.1kHz WAV recording with sounddevice
5. **Stop Recording**: Second hotkey press stops recording and starts processing
6. **Audio Validation**: RMS level analysis detects empty/silent audio before transcription
7. **Smart Processing**: 
   - **Valid audio detected** → Send to Thomson Reuters LiteLLM proxy
   - **Empty/silent audio** → Show "❌ ERROR" status with system tray notification
8. **Smart Text Handling**: 
   - **Successful transcription + Active text field detected** → Auto-inject with pynput
   - **Successful transcription + No active field** → Show smart popup with copy option
   - **Failed transcription** → Show error status and keep audio file for debugging
9. **Return to Background**: Status overlay auto-hides, app remains in system tray

### Secondary Use Case: Settings Access (✅ IMPLEMENTED)

**Configuration Interface:**
1. **Settings Access**: Right-click system tray icon → Settings  
2. **API Configuration**: CustomTkinter GUI for LiteLLM credentials (API key, base URL, alias)
3. **Hotkey Customization**: Configure global hotkey combination
4. **Audio Preferences**: Device selection dropdown with live detection
5. **Theme Settings**: Dark/Light mode toggle with system integration
6. **Notification Settings**: Configure tray notification preferences

### Smart UI Decision Logic (✅ IMPLEMENTED)

**Intelligent Context-Aware Behavior in app.py:**
```python
async def _stop_recording(self):
    """Implemented audio processing with validation"""
    
    # 1. Stop recording and get audio file
    audio_file_path = self.audio_recorder.stop_recording()
    
    # 2. Advanced audio validation with detailed feedback
    quality_metrics = self.audio_recorder.get_quality_metrics(audio_file_path)
    
    if not quality_metrics.has_voice:
        # Show error status and notification
        self.status_dialog.show_error()
        # Clean up invalid audio file
        Path(audio_file_path).unlink(missing_ok=True)
        return
    
    # 3. Show processing status
    self.status_dialog.show_processing()
    
    # 4. Transcribe audio via LiteLLM
    transcribed_text = await self.transcription_service.transcribe_audio(audio_file_path)
    
    # 5. Handle transcription result
    await self._handle_transcription_result(transcribed_text)

async def _handle_transcription_result(self, text: str):
    """Smart text injection with fallback"""
    
    # Try auto-injection using Windows API detection
    success = self.text_injection_service.inject_text(text)
    
    if success:
        # Show success animation
        self.status_dialog.show_success()
    else:
        # Hide status and show smart popup
        self.status_dialog.hide()
        self.current_popup = show_smart_popup(text, context="injection_failed")
```

**Smart Popup Features:**
- **Small, focused window** with transcription text or status message
- **Quick actions**: Copy (Ctrl+C), Paste to active app (Enter), Dismiss (Escape)
- **Auto-positioning** near cursor or screen center
- **Auto-dismiss** after action or 10-second timeout
- **Smart notifications**: Clear feedback for empty audio or recording issues
- **Keyboard-first** interaction for Windows users

---

## 📊 Development Status & Implementation

### Current Implementation Status ✅

## Core Features Implemented ✅

### Foundation Components ✅
| Component | Description | Status | Implementation |
|-----------|-------------|--------|----------------|
| Project Structure | Python package structure | ✅ COMPLETE | Full src/windvoice/ structure |
| Configuration System | TOML config for API credentials | ✅ COMPLETE | ConfigManager with validation |
| System Tray Integration | pystray menu bar presence | ✅ COMPLETE | SystemTrayService with icons |
| Global Hotkeys | pynput hotkey registration | ✅ COMPLETE | HotkeyManager with async callbacks |

### Audio Processing Pipeline ✅
| Component | Description | Status | Implementation |
|-----------|-------------|--------|----------------|
| Audio Recording | sounddevice implementation | ✅ COMPLETE | AudioRecorder with quality metrics |
| WAV File Export | High-quality 44.1kHz output | ✅ COMPLETE | Optimized for Whisper processing |
| Audio Validation | RMS level & silence detection | ✅ COMPLETE | Advanced validation with thresholds |
| LiteLLM Integration | aiohttp POST to proxy | ✅ COMPLETE | TranscriptionService with retry logic |
| Error Handling | User-friendly notifications | ✅ COMPLETE | System tray + status overlay feedback |

### Text Injection System ✅
| Component | Description | Status | Implementation |
|-----------|-------------|--------|----------------|
| Text Injection Service | pynput keyboard automation | ✅ COMPLETE | Multiple injection methods |
| Active Field Detection | Windows API text field detection | ✅ COMPLETE | WindowsTextFieldDetector class |
| Smart Popup | Fallback popup with copy/paste | ✅ COMPLETE | show_smart_popup with context awareness |

### User Interface ✅
| Component | Description | Status | Implementation |
|-----------|-------------|--------|----------------|
| Settings Window | CustomTkinter configuration GUI | ✅ COMPLETE | SettingsWindow with theme support |
| Status Feedback System | Visual recording/processing indicators | ✅ COMPLETE | Multiple status dialog implementations |
| Non-focusable Overlay | Preserve text field focus | ✅ COMPLETE | SimpleVisibleStatusManager with Win32 API |
| Theme System | Dark/Light mode integration | ✅ COMPLETE | Integrated with CustomTkinter themes |

**Implementation Status**: Fully functional voice dictation application ready for daily use

## Future Enhancements (Potential Improvements)

### Build & Distribution 🚀
| Task | Description | Priority |
|------|-------------|----------|
| PyInstaller Setup | Single executable build configuration | High |
| Icon & Assets | Proper icon integration and asset bundling | Medium |
| Windows Installer | MSI installer for easy distribution | Medium |

### Additional Features 🔬
| Task | Description | Priority |
|------|-------------|----------|
| Test Suite | Comprehensive automated testing | High |
| Performance Optimization | Memory usage and startup time tuning | Medium |
| Multiple Audio Formats | Support additional audio formats | Low |
| Advanced Configuration | More detailed user preferences | Low |

---

## 🎯 Implementation Status & Requirements Met

### Functional Requirements ✅ ACHIEVED
- ✅ **Global hotkey activation** - HotkeyManager with pynput integration
- ✅ **Instant recording start** - AudioRecorder with sounddevice pre-initialization
- ✅ **High-quality audio capture** - 44.1kHz, 16-bit WAV optimized for Whisper
- ✅ **Reliable transcription** - TranscriptionService with Thomson Reuters LiteLLM proxy
- ✅ **Smart text injection** - WindowsTextFieldDetector + multiple injection methods
- ✅ **Context-aware UI** - Smart popup fallback when injection fails
- ✅ **Background operation** - SystemTrayService with minimal resource usage
- ✅ **Windows compatibility** - Native Windows API integration via pywin32

### Performance Requirements ✅ ACHIEVED
- 🚀 **Memory Usage**: Optimized Python application with efficient resource management
- ⚡ **Startup Time**: Fast initialization with system tray integration
- 🎤 **Recording Latency**: Instant hotkey response with pre-initialized audio system
- 🤖 **Transcription Speed**: Efficient aiohttp integration with Thomson Reuters proxy
- 💉 **Text Injection**: Optimized Windows API text field detection and injection
- 🔄 **Background CPU**: Minimal impact with event-driven architecture

### Quality Requirements ✅ IMPLEMENTED
- 🧪 **Testing**: test_text_detection.py for core text injection functionality
- 🛡️ **Error Handling**: Comprehensive exception handling with user-friendly messages
- 🔒 **Security**: 
  - ✅ TOML config files in user home directory (~/.windvoice/config.toml)
  - ✅ Never log API keys or sensitive data (WindVoiceLogger with filtering)
  - ✅ ConfigManager with validation and secure storage
- 📊 **Reliability**: Graceful error recovery with audio file debugging
- 🎧 **Audio Validation**: RMS level analysis with quality metrics
- 📝 **Smart Notifications**: Context-aware system tray notifications
  - ✅ "❌ No voice detected in recording"
  - ✅ "⚠️ Microphone is currently being used by another application"
  - ✅ "✅ Text injected successfully"

### User Experience Requirements ✅ ACHIEVED
- 📱 **Intuitive UI**: Simple system tray interface with context menus
- 🚀 **Responsive Feedback**: SimpleVisibleStatusManager with real-time status overlays
- 🎯 **Smart Behavior**: WindowsTextFieldDetector with intelligent injection vs popup logic
- 🔧 **Customizable**: SettingsWindow for hotkeys, themes, and API configuration
- 📞 **Accessibility**: Non-focusable overlays preserve text field focus for screen readers

---

## ⚙️ Configuration & LiteLLM Setup

### Configuration

See the [Installation Guide](INSTALLER_GUIDE.md) for complete configuration instructions and the [API Documentation](API.md) for LiteLLM integration details.

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

**Document Version**: 3.0  
**Created**: 2025-01-09  
**Last Updated**: 2025-01-29  
**Target Audience**: Development team and stakeholders  
**Status**: ✅ MVP COMPLETE - Core functionality fully implemented and ready for use

**Key Success Factors Achieved**: 
- ✅ **Simple system tray integration** - Clean system tray presence with instant hotkey activation
- ✅ **Seamless text injection** - WindowsTextFieldDetector with smart popup fallback  
- ✅ **Minimal user interface complexity** - Non-focusable overlays preserve workflow
- ✅ **Production-ready reliability** - Comprehensive error handling and audio validation

**Current Status**: Fully functional voice dictation application ready for daily use with complete Windows integration.