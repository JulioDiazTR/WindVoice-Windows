import asyncio
import sys
from pathlib import Path
from typing import Optional
import tkinter as tk
import customtkinter as ctk

from .config import ConfigManager, WindVoiceConfig
from .exceptions import WindVoiceError, ConfigurationError, AudioError, TranscriptionError
from ..services.audio import AudioRecorder, AudioValidation
from ..services.transcription import TranscriptionService
from ..services.injection import TextInjectionService
from ..services.hotkeys import HotkeyManager
from ..ui.menubar import SystemTrayService
from ..ui.settings import SettingsWindow
from ..ui.popup import show_smart_popup
from ..ui.simple_visible_status import SimpleVisibleStatusManager
from ..utils.logging import get_logger, WindVoiceLogger, setup_logging


class WindVoiceApp:
    def __init__(self):
        # Setup comprehensive logging first
        self.logger = setup_logging("DEBUG", True)
        
        WindVoiceLogger.log_audio_workflow_step(
            self.logger,
            "WindVoiceApp_Initializing",
            {"timestamp": asyncio.get_event_loop().time() if asyncio._get_running_loop() else "no_loop"}
        )
        
        self.config_manager = ConfigManager()
        self.config: Optional[WindVoiceConfig] = None
        
        # Services
        self.audio_recorder: Optional[AudioRecorder] = None
        self.transcription_service: Optional[TranscriptionService] = None
        self.text_injection_service: Optional[TextInjectionService] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.system_tray: Optional[SystemTrayService] = None
        
        # UI
        self.root_window: Optional[tk.Tk] = None
        self.settings_window: Optional[SettingsWindow] = None
        self.current_popup = None
        self.status_dialog: Optional[SimpleVisibleStatusManager] = None
        
        # State
        self.recording = False
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False
        
        # Real-time feedback
        self.level_monitor_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        try:
            # Initialize Tkinter root window for UI components
            self._initialize_ui_root()
            
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
    
    def _initialize_ui_root(self):
        """Initialize the root Tkinter window (hidden)"""
        try:
            # Create invisible root window for CustomTkinter
            self.root_window = ctk.CTk()
            self.root_window.withdraw()  # Hide the window
            
            # Configure CustomTkinter
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
        except Exception as e:
            raise WindVoiceError(f"Failed to initialize UI root: {e}")
    
    async def _initialize_services(self):
        self.logger.info("Starting service initialization...")
        
        # Audio recorder
        self.logger.info("Initializing AudioRecorder...")
        self.audio_recorder = AudioRecorder(
            sample_rate=self.config.app.sample_rate,
            device=self.config.app.audio_device
        )
        self.logger.info("AudioRecorder initialized successfully")
        
        # Transcription service
        self.logger.info("Initializing TranscriptionService...")
        self.transcription_service = TranscriptionService(self.config.litellm)
        self.logger.info("TranscriptionService initialized successfully")
        
        # Text injection service
        self.logger.info("Initializing TextInjectionService...")
        self.text_injection_service = TextInjectionService()
        self.logger.info("TextInjectionService initialized successfully")
        
        # Hotkey manager
        self.logger.info("Initializing HotkeyManager...")
        self.hotkey_manager = HotkeyManager()
        self.logger.info("Setting hotkey configuration...")
        self.hotkey_manager.set_hotkey(self.config.app.hotkey)
        self.hotkey_manager.set_hotkey_callback(self._on_hotkey_pressed)
        self.logger.info("HotkeyManager initialized successfully")
        
        # System tray
        self.logger.info("Initializing SystemTrayService...")
        self.system_tray = SystemTrayService(
            on_settings=self._show_settings,
            on_quit=self._quit_application
        )
        self.logger.info("SystemTrayService initialized successfully")
        
        # Settings window
        self.logger.info("Initializing SettingsWindow...")
        self.settings_window = SettingsWindow(self.config_manager, self.audio_recorder)
        self.logger.info("SettingsWindow initialized successfully")
        
        # Status dialog for visual feedback
        self.logger.info("Initializing SimpleVisibleStatusManager...")
        self.status_dialog = SimpleVisibleStatusManager()
        self.logger.info("SimpleVisibleStatusManager initialized successfully")
        
        self.logger.info("All services initialized successfully")
    
    async def start(self):
        if self.running:
            self.logger.info("App already running, skipping start")
            return
            
        self.logger.info("Starting WindVoice application...")
        self.event_loop = asyncio.get_event_loop()
        self.running = True
        
        try:
            # Start services
            self.logger.info("Starting HotkeyManager...")
            self.hotkey_manager.start(self.event_loop)
            self.logger.info("HotkeyManager started successfully")
            
            self.logger.info("Starting SystemTrayService...")
            self.system_tray.start(self.event_loop)
            self.logger.info("SystemTrayService started successfully")
            
            # Show startup notification
            if self.config.ui.show_tray_notifications:
                self.logger.info("Showing startup notification...")
                self.system_tray.show_notification(
                    "WindVoice Started",
                    f"Press {self.config.app.hotkey} to start recording"
                )
            
            print(f"WindVoice is running. Press {self.config.app.hotkey} to record.")
            self.logger.info("WindVoice startup completed - entering main loop")
            
            # Keep the application running and process Tkinter events
            loop_counter = 0
            while self.running:
                # Log every 100 iterations (10 seconds) to show we're alive
                if loop_counter % 100 == 0:
                    self.logger.debug(f"Main loop iteration {loop_counter}")
                
                # Process Tkinter events if root window exists
                if self.root_window:
                    try:
                        self.root_window.update()
                    except tk.TclError:
                        # Window was destroyed
                        self.logger.warning("Root window was destroyed - stopping app")
                        break
                        
                await asyncio.sleep(0.1)
                loop_counter += 1
                
        except Exception as e:
            self.logger.error(f"Error starting WindVoice: {e}")
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
        
        # Hide status dialog
        if self.status_dialog:
            self.status_dialog.hide()
        
        # Close UI root window
        if self.root_window:
            try:
                self.root_window.quit()
                self.root_window.destroy()
            except:
                pass
        
        print("WindVoice stopped")
    
    async def _on_hotkey_pressed(self):
        WindVoiceLogger.log_hotkey_event(
            self.logger,
            "HOTKEY_PRESSED",
            {
                "currently_recording": self.recording,
                "app_running": self.running,
                "audio_recorder_exists": self.audio_recorder is not None
            }
        )
        
        try:
            if self.recording:
                self.logger.info("STOP: Hotkey pressed: STOPPING recording")
                await self._stop_recording()
            else:
                self.logger.info("START: Hotkey pressed: STARTING recording")
                await self._start_recording()
        except Exception as e:
            self.logger.error(f"Hotkey handler failed: {e}")
            WindVoiceLogger.log_hotkey_event(
                self.logger,
                "HOTKEY_ERROR",
                {"error": str(e), "recording_state": self.recording}
            )
            self._show_error_notification("Hotkey Error", str(e))
    
    async def _start_recording(self):
        WindVoiceLogger.log_audio_workflow_step(
            self.logger,
            "_start_recording_CALLED",
            {
                "current_recording_state": self.recording,
                "audio_recorder_ready": self.audio_recorder is not None,
                "system_tray_ready": self.system_tray is not None
            }
        )
        
        try:
            self.recording = True
            self.system_tray.set_recording_state(True)
            
            # Show fast visual feedback in the main UI thread
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_recording)
            
            # Start real-time level monitoring
            self.level_monitor_task = asyncio.create_task(self._monitor_recording_levels())
            
            self.logger.info("Calling audio_recorder.start_recording()...")
            self.audio_recorder.start_recording()
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Start_SUCCESS",
                {"state_updated": True, "level_monitor_started": True}
            )
            
        except AudioError as e:
            self.logger.error(f"AudioError in _start_recording: {e}")
            self.recording = False
            self.system_tray.set_recording_state(False)
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Start_AUDIO_ERROR",
                {"error": str(e)}
            )
        except Exception as e:
            self.logger.error(f"General error in _start_recording: {e}")
            self.recording = False
            self.system_tray.set_recording_state(False)
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Start_GENERAL_ERROR",
                {"error": str(e)}
            )
    
    async def _monitor_recording_levels(self):
        """Monitor recording levels for visual feedback"""
        try:
            while self.recording:
                if self.audio_recorder and self.audio_recorder.is_recording():
                    level = self.audio_recorder.get_current_level()
                    # Update both system tray and status dialog
                    self.system_tray.update_recording_level(level)
                    self.status_dialog.update_audio_level(level)
                    
                await asyncio.sleep(0.1)  # Update 10 times per second
                
        except Exception as e:
            print(f"Level monitoring error: {e}")
    
    async def _stop_recording(self):
        WindVoiceLogger.log_audio_workflow_step(
            self.logger,
            "_stop_recording_CALLED",
            {
                "current_recording_state": self.recording,
                "level_monitor_active": self.level_monitor_task is not None,
                "audio_recorder_ready": self.audio_recorder is not None
            }
        )
        
        try:
            # Stop level monitoring
            if self.level_monitor_task:
                self.logger.debug("Cancelling level monitor task...")
                self.level_monitor_task.cancel()
                try:
                    await self.level_monitor_task
                except asyncio.CancelledError:
                    pass
                self.level_monitor_task = None
            
            # Stop recording and get audio file
            self.logger.info("Calling audio_recorder.stop_recording()...")
            audio_file_path = self.audio_recorder.stop_recording()
            self.recording = False
            self.system_tray.set_recording_state(False)
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_File_Created",
                {"file_path": audio_file_path, "file_exists": Path(audio_file_path).exists()}
            )
            
            # Advanced audio validation with detailed feedback
            self.logger.info("Starting audio validation...")
            quality_metrics = self.audio_recorder.get_quality_metrics(audio_file_path)
            title, message = self.audio_recorder.get_validation_message(audio_file_path)
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_Validation_Complete",
                {
                    "has_voice": quality_metrics.has_voice,
                    "quality_score": quality_metrics.quality_score,
                    "rms_level": quality_metrics.rms_level,
                    "duration": quality_metrics.duration
                }
            )
            
            if not quality_metrics.has_voice:
                self.logger.info(f"No voice detected - showing error state")
                if self.root_window:
                    self.root_window.after(0, self.status_dialog.show_error)
                # Clean up the invalid audio file
                Path(audio_file_path).unlink(missing_ok=True)
                WindVoiceLogger.log_audio_workflow_step(
                    self.logger,
                    "No_Voice_Detected_Cleanup",
                    {"file_deleted": True}
                )
                return
            
            # Show processing animation in the main UI thread
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_processing)
            
            # Transcribe audio
            self.logger.info("Starting transcription...")
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Transcription_Started",
                {"file_path": audio_file_path}
            )
            
            transcribed_text = await self.transcription_service.transcribe_audio(audio_file_path)
            
            # Keep audio file for debugging if transcription fails
            transcription_successful = bool(transcribed_text and transcribed_text.strip())
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Transcription_Complete",
                {
                    "successful": transcription_successful,
                    "text_length": len(transcribed_text) if transcribed_text else 0,
                    "text_preview": transcribed_text[:50] + "..." if transcribed_text and len(transcribed_text) > 50 else transcribed_text
                }
            )
            
            if not transcription_successful:
                self.logger.warning(f"Transcription failed - keeping audio file for debugging")
                if self.root_window:
                    self.root_window.after(0, self.status_dialog.show_error)
                # Don't delete the file so user can inspect it
                print(f"Transcription failed - audio file kept at: {audio_file_path}")
                WindVoiceLogger.log_audio_workflow_step(
                    self.logger,
                    "Transcription_Failed_Debug",
                    {"debug_file_path": audio_file_path}
                )
                return
            else:
                # Clean up successful audio file
                Path(audio_file_path).unlink(missing_ok=True)
                WindVoiceLogger.log_audio_workflow_step(
                    self.logger,
                    "Transcription_Success_Cleanup",
                    {"file_deleted": True}
                )
            
            # Handle transcription result
            await self._handle_transcription_result(transcribed_text)
            
        except AudioError as e:
            self.logger.error(f"AudioError in _stop_recording: {e}")
            await self._cleanup_recording_state()
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Stop_AUDIO_ERROR",
                {"error": str(e)}
            )
        except TranscriptionError as e:
            self.logger.error(f"TranscriptionError in _stop_recording: {e}")
            await self._cleanup_recording_state()
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Stop_TRANSCRIPTION_ERROR",
                {"error": str(e)}
            )
        except Exception as e:
            self.logger.error(f"General error in _stop_recording: {e}")
            await self._cleanup_recording_state()
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Stop_GENERAL_ERROR",
                {"error": str(e)}
            )
    
    async def _cleanup_recording_state(self):
        """Clean up recording state after error"""
        if self.level_monitor_task:
            self.level_monitor_task.cancel()
            try:
                await self.level_monitor_task
            except asyncio.CancelledError:
                pass
            self.level_monitor_task = None
            
        self.recording = False
        self.system_tray.set_recording_state(False)
    
    async def _handle_transcription_result(self, text: str):
        try:
            # Try to inject text directly
            success = self.text_injection_service.inject_text(text)
            
            if success:
                # Show success animation and auto-close
                if self.root_window:
                    self.root_window.after(0, self.status_dialog.show_success)
            else:
                # Hide status dialog and show smart popup for text copy
                if self.root_window:
                    self.root_window.after(0, self.status_dialog.hide)
                self.current_popup = show_smart_popup(
                    text, 
                    context="injection_failed",
                    timeout=15
                )
                
        except Exception as e:
            # Show error state briefly, then fallback to popup
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
                # Schedule popup after error display
                self.root_window.after(1000, lambda: self._show_injection_error_popup(text))
            else:
                self.current_popup = show_smart_popup(
                    text, 
                    context="injection_error",
                    timeout=20
                )
    
    def _show_injection_error_popup(self, text: str):
        """Helper method to show injection error popup"""
        self.status_dialog.hide()
        self.current_popup = show_smart_popup(
            text, 
            context="injection_error",
            timeout=20
        )
    
    def _show_smart_notification(self, title: str, message: str, is_error: bool = False):
        """Show intelligent notifications with better formatting"""
        if self.system_tray:
            # Add emoji indicators
            if is_error:
                display_title = f"❌ {title}"
            elif "success" in title.lower() or "✅" in title:
                display_title = f"✅ {title}"
            elif "warning" in title.lower():
                display_title = f"⚠️ {title}"
            else:
                display_title = f"ℹ️ {title}"
                
            self.system_tray.show_notification(display_title, message)
            
        # Also log with appropriate level
        log_level = "ERROR" if is_error else "INFO"
        print(f"{log_level} - {title}: {message}")
    
    def _show_error_notification(self, title: str, message: str):
        """Legacy method - redirects to smart notifications"""
        self._show_smart_notification(title, message, is_error=True)
    
    def _show_info_notification(self, title: str, message: str):
        """Legacy method - redirects to smart notifications"""
        self._show_smart_notification(title, message, is_error=False)
    
    async def _show_settings(self):
        """Show the settings window"""
        try:
            if self.settings_window:
                self.settings_window.show()
            else:
                self._show_error_notification("Settings Error", "Settings window not available")
        except Exception as e:
            self._show_error_notification("Settings Error", f"Failed to open settings: {e}")
            print(f"Settings error: {e}")
    
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