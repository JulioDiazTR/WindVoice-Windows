import asyncio
import sys
from pathlib import Path
from typing import Optional

from .config import ConfigManager, WindVoiceConfig
from .exceptions import WindVoiceError, ConfigurationError, AudioError, TranscriptionError
from ..services.audio import AudioRecorder, AudioValidation
from ..services.transcription import TranscriptionService
from ..services.injection import TextInjectionService
from ..services.hotkeys import HotkeyManager
from ..ui.menubar import SystemTrayService


class WindVoiceApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config: Optional[WindVoiceConfig] = None
        
        # Services
        self.audio_recorder: Optional[AudioRecorder] = None
        self.transcription_service: Optional[TranscriptionService] = None
        self.text_injection_service: Optional[TextInjectionService] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.system_tray: Optional[SystemTrayService] = None
        
        # State
        self.recording = False
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False
        
    async def initialize(self):
        try:
            # Load configuration
            self.config = self.config_manager.load_config()
            
            # Check if this is first run (no configuration)
            if not self.config_manager.validate_config():
                status = self.config_manager.get_config_status()
                print("\nWindVoice - Configuration Required")
                print("=" * 50)
                print("Thomson Reuters LiteLLM credentials are not configured.")
                print(f"Config file: {status['config_file_path']}")
                print("\nTo configure WindVoice, please run:")
                print("  python setup_config.py")
                print("\nOr manually edit the config file with your LiteLLM credentials.")
                raise ConfigurationError("LiteLLM configuration required. Run 'python setup_config.py' to configure.")
            
            # Initialize services
            await self._initialize_services()
            
            print("WindVoice initialized successfully")
            
        except Exception as e:
            raise WindVoiceError(f"Failed to initialize WindVoice: {e}")
    
    async def _initialize_services(self):
        # Audio recorder
        self.audio_recorder = AudioRecorder(
            sample_rate=self.config.app.sample_rate,
            device=self.config.app.audio_device
        )
        
        # Transcription service
        self.transcription_service = TranscriptionService(self.config.litellm)
        
        # Text injection service
        self.text_injection_service = TextInjectionService()
        
        # Hotkey manager
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.set_hotkey(self.config.app.hotkey)
        self.hotkey_manager.set_hotkey_callback(self._on_hotkey_pressed)
        
        # System tray
        self.system_tray = SystemTrayService(
            on_settings=self._show_settings,
            on_quit=self._quit_application
        )
    
    async def start(self):
        if self.running:
            return
            
        self.event_loop = asyncio.get_event_loop()
        self.running = True
        
        try:
            # Start services
            self.hotkey_manager.start(self.event_loop)
            self.system_tray.start(self.event_loop)
            
            # Show startup notification
            if self.config.ui.show_tray_notifications:
                self.system_tray.show_notification(
                    "WindVoice Started",
                    f"Press {self.config.app.hotkey} to start recording"
                )
            
            print(f"WindVoice is running. Press {self.config.app.hotkey} to record.")
            
            # Keep the application running
            while self.running:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"Error starting WindVoice: {e}")
            await self.stop()
    
    async def stop(self):
        self.running = False
        
        # Stop recording if active
        if self.recording and self.audio_recorder:
            try:
                self.audio_recorder.stop_recording()
            except:
                pass
        
        # Stop services
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        
        if self.system_tray:
            self.system_tray.stop()
        
        if self.transcription_service:
            await self.transcription_service.close()
        
        # Cleanup temp files
        if self.audio_recorder:
            self.audio_recorder.cleanup_temp_files()
        
        print("WindVoice stopped")
    
    async def _on_hotkey_pressed(self):
        try:
            if self.recording:
                await self._stop_recording()
            else:
                await self._start_recording()
        except Exception as e:
            self._show_error_notification("Hotkey Error", str(e))
    
    async def _start_recording(self):
        try:
            self.recording = True
            self.system_tray.set_recording_state(True)
            
            if self.config.ui.show_tray_notifications:
                self.system_tray.show_notification("WindVoice", "Recording started...")
            
            self.audio_recorder.start_recording()
            
        except AudioError as e:
            self.recording = False
            self.system_tray.set_recording_state(False)
            self._show_error_notification("Recording Error", str(e))
        except Exception as e:
            self.recording = False
            self.system_tray.set_recording_state(False)
            self._show_error_notification("Error", f"Failed to start recording: {e}")
    
    async def _stop_recording(self):
        try:
            # Stop recording and get audio file
            audio_file_path = self.audio_recorder.stop_recording()
            self.recording = False
            self.system_tray.set_recording_state(False)
            
            # Validate audio content
            validation = self.audio_recorder.validate_audio_file(audio_file_path)
            
            if not validation.has_voice:
                self._show_info_notification(
                    "No voice detected",
                    "Your recording appears to be silent. Please try again."
                )
                # Clean up the empty audio file
                Path(audio_file_path).unlink(missing_ok=True)
                return
            
            # Show transcription in progress
            if self.config.ui.show_tray_notifications:
                self.system_tray.show_notification("WindVoice", "Transcribing audio...")
            
            # Transcribe audio
            transcribed_text = await self.transcription_service.transcribe_audio(audio_file_path)
            
            # Clean up audio file
            Path(audio_file_path).unlink(missing_ok=True)
            
            if not transcribed_text.strip():
                self._show_info_notification(
                    "Transcription empty",
                    "Audio was processed but no text was generated."
                )
                return
            
            # Handle transcription result
            await self._handle_transcription_result(transcribed_text)
            
        except AudioError as e:
            self.recording = False
            self.system_tray.set_recording_state(False)
            self._show_error_notification("Recording Error", str(e))
        except TranscriptionError as e:
            self.recording = False
            self.system_tray.set_recording_state(False)
            self._show_error_notification("Transcription Error", str(e))
        except Exception as e:
            self.recording = False
            self.system_tray.set_recording_state(False)
            self._show_error_notification("Error", f"Failed to process recording: {e}")
    
    async def _handle_transcription_result(self, text: str):
        try:
            # Try to inject text directly
            success = self.text_injection_service.inject_text(text)
            
            if success:
                if self.config.ui.show_tray_notifications:
                    self.system_tray.show_notification("WindVoice", "✅ Text injected successfully")
            else:
                # Fallback: show popup (not implemented in MVP)
                self._show_info_notification("Transcription Result", f"Text: {text}")
                
        except Exception as e:
            self._show_error_notification("Text Injection Error", str(e))
            # Fallback: show the text in notification
            self._show_info_notification("Transcription Result", f"Text: {text}")
    
    def _show_error_notification(self, title: str, message: str):
        if self.system_tray:
            self.system_tray.show_notification(title, message)
        print(f"ERROR - {title}: {message}")
    
    def _show_info_notification(self, title: str, message: str):
        if self.system_tray:
            self.system_tray.show_notification(title, message)
        print(f"INFO - {title}: {message}")
    
    async def _show_settings(self):
        # TODO: Implement settings dialog in Sprint 2
        self._show_info_notification("Settings", "Settings dialog not implemented yet")
        print("Settings requested - not implemented in MVP")
    
    async def _quit_application(self):
        print("Quit requested")
        await self.stop()


# Main entry point
async def main():
    app = WindVoiceApp()
    
    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())