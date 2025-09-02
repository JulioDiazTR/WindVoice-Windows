# WindVoice-Windows Architecture Documentation

## Overview

WindVoice-Windows is a native Windows voice dictation application built with 100% Python. It follows a single-process, event-driven architecture optimized for low latency and minimal resource usage. The application lives in the system tray and provides global hotkey activation for voice recording and transcription.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  WindVoice Python App                      │
│                    (Single Process)                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              UI Layer (CustomTkinter)                   │ │
│  │  ┌──────────────┬────────────────┬──────────────────┐  │ │
│  │  │ System Tray  │ Settings Panel │ Status Dialogs   │  │ │
│  │  │ (pystray)    │               │ & Popups         │  │ │
│  │  └──────────────┴────────────────┴──────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   Services Layer                        │ │
│  │  ┌──────────────┬────────────────┬──────────────────┐  │ │
│  │  │ Audio        │ Hotkey         │ Text Injection   │  │ │
│  │  │ Service      │ Manager        │ Service          │  │ │
│  │  └──────────────┴────────────────┴──────────────────┘  │ │
│  │  ┌──────────────┬────────────────┬──────────────────┐  │ │
│  │  │ Transcription│ Audio          │ System Tray      │  │ │
│  │  │ Service      │ Validation     │ Service          │  │ │
│  │  └──────────────┴────────────────┴──────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Core Layer                              │ │
│  │  • Application Controller (WindVoiceApp)               │ │
│  │  • Configuration Management (TOML)                     │ │
│  │  • Exception Handling                                  │ │
│  │  • Logging System                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS API Calls
                              ▼
      ┌─────────────────────────────────────────┐
      │     Thomson Reuters LiteLLM Proxy       │
      │         (External Service)              │
      │  • OpenAI Whisper-1 Model              │
      │  • Authentication via API Key          │
      │  • Usage Tracking via Key Alias       │
      └─────────────────────────────────────────┘
```

## Component Architecture

### Core Layer

#### 1. Application Controller (`windvoice.core.app.WindVoiceApp`)

The main application controller that orchestrates all services and handles the application lifecycle.

**Key Responsibilities:**
- Service initialization and lifecycle management
- Event coordination between services
- Main event loop management
- Error handling and recovery

**Design Patterns:**
- Singleton pattern for application instance
- Observer pattern for service communication
- Command pattern for hotkey handling

#### 2. Configuration Management (`windvoice.core.config`)

TOML-based configuration system with validation and defaults.

**Features:**
- Type-safe configuration with dataclasses
- Automatic default value generation
- Configuration validation
- Runtime configuration updates

**Configuration Structure:**
```toml
[litellm]
api_key = "sk-..."
api_base = "https://..."
key_alias = "user-identifier"
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

### Services Layer

#### 1. Audio Service (`windvoice.services.audio`)

High-performance audio recording with real-time monitoring.

**Architecture:**
- **Recording Engine**: sounddevice for low-latency capture
- **Format**: 44.1kHz WAV optimized for Whisper
- **Monitoring**: Real-time level monitoring with 10Hz updates
- **Validation**: Pre-transcription audio quality assessment

**Key Features:**
- Device enumeration and selection
- Automatic gain control
- Silent recording detection
- Temporary file management

#### 2. Audio Validation (`windvoice.utils.audio_validation`)

Advanced audio quality assessment system.

**Validation Pipeline:**
1. **Basic Analysis**: RMS levels, peak detection, duration
2. **Voice Activity Detection**: Frame-based energy analysis
3. **Noise Assessment**: Background noise level estimation
4. **Quality Scoring**: 0-100 quality score calculation

**Metrics Provided:**
```python
@dataclass
class AudioQualityMetrics:
    has_voice: bool
    rms_level: float
    voice_activity_ratio: float
    noise_level: float
    dynamic_range: float
    quality_score: float  # 0-100
```

#### 3. Transcription Service (`windvoice.services.transcription`)

LiteLLM integration with retry logic and connection management.

**Architecture:**
- **HTTP Client**: aiohttp with session pooling
- **Retry Logic**: 3 attempts with exponential backoff
- **Request Uniqueness**: UUID-based request IDs to prevent caching
- **Connection Management**: Fresh sessions for each request

**API Integration:**
```python
# Request format
POST /v1/audio/transcriptions
Headers:
  Authorization: Bearer {api_key}
  X-Key-Alias: {key_alias}
  X-Request-ID: {unique_id}
  Cache-Control: no-cache
Form Data:
  file: audio_{timestamp}_{request_id}.wav
  model: whisper-1
  response_format: json
```

#### 4. Hotkey Manager (`windvoice.services.hotkeys`)

Global hotkey handling with Windows integration.

**Features:**
- Cross-application hotkey capture
- Configurable key combinations
- Asynchronous callback system
- Conflict detection and resolution

#### 5. Text Injection Service (`windvoice.services.injection`)

Multi-method text injection for Windows applications.

**Injection Methods:**
1. **Direct Typing**: pynput keyboard simulation
2. **Clipboard Method**: Copy + paste fallback
3. **Windows API**: Direct window messaging (planned)

#### 6. System Tray Service (`windvoice.ui.menubar`)

System tray integration with visual feedback.

**Features:**
- Icon animation during recording
- Real-time level indicators
- Context menu management
- Notification system

### User Interface Layer

#### 1. Status Dialogs (`windvoice.ui.status_dialog`, etc.)

Visual feedback system with multiple dialog types:

- **SimpleVisibleStatusManager**: Basic status with transparency
- **RobustStatusDialog**: Advanced status with animations
- **TransparentDialog**: Ultra-minimal status display

**Design Principles:**
- Minimal visual intrusion
- Fast display/hide animations
- Real-time audio level display
- Auto-positioning near cursor

#### 2. Settings Window (`windvoice.ui.settings`)

Configuration interface with live validation.

**Features:**
- Real-time configuration validation
- Audio device testing
- LiteLLM connection testing
- Configuration export/import

#### 3. Smart Popup (`windvoice.ui.popup`)

Context-aware transcription result display.

**Behaviors:**
- **Auto-injection success**: Brief confirmation
- **Injection failure**: Copy-friendly popup
- **Transcription error**: Error display with retry options

## Data Flow Architecture

### Recording Workflow

```
User Hotkey Press
    ↓
HotkeyManager.callback()
    ↓
WindVoiceApp._start_recording()
    ↓
AudioRecorder.start_recording()
    ↓
Real-time level monitoring
    ↓
User Hotkey Press (stop)
    ↓
AudioRecorder.stop_recording()
    ↓
AudioValidator.validate_audio()
    ↓
[If valid] TranscriptionService.transcribe()
    ↓
TextInjectionService.inject_text()
    ↓
[Success] Show confirmation
[Failure] Show popup with text
```

### Configuration Flow

```
Application Start
    ↓
ConfigManager.load_config()
    ↓
[If missing] Create defaults
    ↓
ConfigManager.validate_config()
    ↓
[If invalid] Show configuration prompt
    ↓
Initialize services with config
    ↓
Runtime updates via SettingsWindow
    ↓
ConfigManager.save_config()
```

## Thread and Async Architecture

### Threading Model

- **Main Thread**: Tkinter event loop, UI updates
- **Async Event Loop**: Service coordination, I/O operations
- **Audio Thread**: Real-time audio capture (managed by sounddevice)
- **Hotkey Thread**: Global hotkey listening (managed by pynput)

### Async Patterns

```python
# Service initialization
async def _initialize_services(self):
    # All services initialized sequentially
    # to ensure proper dependency order

# Recording workflow
async def _stop_recording(self):
    # Async transcription request
    text = await self.transcription_service.transcribe_audio(path)
    # UI updates scheduled on main thread
    self.root_window.after(0, self.status_dialog.show_success)
```

## Error Handling Architecture

### Exception Hierarchy

```
WindVoiceError (base)
├── ConfigurationError
├── AudioError
├── TranscriptionError
└── InjectionError
```

### Error Handling Strategy

1. **Service Level**: Catch specific errors, log details
2. **Application Level**: Convert to user-friendly messages
3. **UI Level**: Display appropriate error dialogs
4. **Recovery**: Automatic retry with exponential backoff

### Logging Architecture

**Log Levels:**
- **DEBUG**: Detailed execution flow
- **INFO**: Important application events  
- **WARNING**: Recoverable issues
- **ERROR**: Critical failures

**Log Categories:**
- **Audio Workflow**: Recording → validation → transcription
- **Hotkey Events**: Key press handling and state changes
- **API Requests**: LiteLLM communication details
- **Configuration**: Settings validation and updates

## Performance Architecture

### Memory Management

- **Audio Buffers**: Automatic cleanup after transcription
- **Session Pooling**: Fresh HTTP sessions to prevent memory leaks
- **UI Components**: Lazy initialization and cleanup

### Optimization Strategies

1. **Pre-initialized Services**: All services ready at startup
2. **Efficient Audio Processing**: sounddevice with optimal buffer sizes  
3. **Smart Validation**: Skip transcription for invalid audio
4. **Connection Management**: Session cleanup after each request

### Performance Targets

- **Memory Usage**: <50MB baseline
- **Startup Time**: <2 seconds to ready state
- **Recording Latency**: <100ms hotkey to recording start
- **Transcription**: <3 seconds for 10-second audio clips

## Security Architecture

### Credential Management

- **Storage**: User home directory (`~/.windvoice/config.toml`)
- **Access**: File system permissions only
- **Logging**: Never log API keys or sensitive data
- **Validation**: Configuration validation without exposure

### API Security

- **Transport**: HTTPS only with certificate validation
- **Authentication**: Bearer token with Thomson Reuters proxy
- **Request Uniqueness**: UUID-based request IDs
- **Retry Logic**: Secure failure handling without credential exposure

## Extensibility Architecture

### Plugin Architecture (Future)

The current architecture supports future plugin extensions:

```python
# Plugin interface (planned)
class WindVoicePlugin:
    def on_transcription_complete(self, text: str) -> str:
        """Modify transcribed text before injection"""
        pass
    
    def on_audio_recorded(self, audio_path: str) -> bool:
        """Process audio before transcription"""
        pass
```

### Service Interface Pattern

All services implement consistent interfaces for easy replacement:

```python
class AudioRecorder:
    def start_recording(self) -> None: ...
    def stop_recording(self) -> str: ...  # Returns file path
    def get_current_level(self) -> float: ...

class TranscriptionService:
    async def transcribe_audio(self, path: str) -> str: ...
    async def test_connection(self) -> tuple[bool, str]: ...
```

## Deployment Architecture

### Single Executable

- **Builder**: PyInstaller with optimized bundling
- **Size Target**: ~35MB installer
- **Dependencies**: All Python packages bundled
- **Assets**: Icons and sounds embedded

### Windows Integration

- **Registry**: Optional startup entry
- **File Associations**: Audio file handling (planned)
- **Shell Integration**: Right-click context menu (planned)

## Quality Architecture

### Testing Strategy

- **Unit Tests**: Individual service validation
- **Integration Tests**: Complete workflow testing
- **Performance Tests**: Memory and latency monitoring
- **Windows Tests**: Multi-version Windows compatibility

### Monitoring and Observability

- **Structured Logging**: JSON-formatted log entries
- **Performance Metrics**: Built-in timing and memory tracking  
- **Health Checks**: Service validation and connectivity testing
- **Crash Reporting**: Detailed error context capture

This architecture provides a solid foundation for a production-ready voice dictation application while maintaining simplicity and performance.