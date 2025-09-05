import asyncio
import sys
from pathlib import Path
from typing import Optional
import tkinter as tk
import customtkinter as ctk

from .config import ConfigManager, WindVoiceConfig
from .exceptions import WindVoiceError, ConfigurationError, AudioError, AudioDeviceBusyError, TranscriptionError
from ..services.audio import AudioRecorder, AudioValidation
from ..services.transcription import TranscriptionService
from ..services.injection import TextInjectionService
from ..services.hotkeys import HotkeyManager
from ..ui.menubar import SystemTrayService
from ..ui.settings import SettingsWindow
from ..ui.popup import show_smart_popup
from ..ui.simple_visible_status import SimpleVisibleStatusManager
from ..ui.setup_wizard import run_setup_if_needed
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
            
            # Check if initial setup is needed
            setup_launched = run_setup_if_needed(self.config_manager, self._on_setup_complete)
            if setup_launched:
                self.logger.info("Setup wizard launched - waiting for completion")
                return  # Setup wizard will handle the rest
            
            # If setup was needed but couldn't be launched (e.g., headless environment)
            # try to load config anyway - the setup wizard might have provided guidance
            if not self.config_manager.config_exists():
                self.logger.error("No configuration found and setup wizard could not run")
                self.logger.error("Please create configuration manually or run in GUI environment")
                raise ConfigurationError("Configuration required but setup wizard unavailable")
                
            # Continue with normal initialization
            
            # Load configuration (setup is complete)
            self.config = self.config_manager.load_config()
            
            # Configure theme based on loaded config
            self._apply_theme()
            
            # Double-check configuration validity
            if not self.config_manager.validate_config():
                status = self.config_manager.get_config_status()
                print("\nWindVoice - Configuration Invalid")
                print("=" * 50)
                print("Thomson Reuters LiteLLM credentials are not properly configured.")
                print(f"Config file: {status['config_file_path']}")
                print("\nPlease check your configuration file or restart the application to run setup again.")
                raise ConfigurationError("LiteLLM configuration is invalid or incomplete.")
            
            # Initialize services
            await self._initialize_services()
            
            print("WindVoice initialized successfully")
            
        except Exception as e:
            raise WindVoiceError(f"Failed to initialize WindVoice: {e}")
    
    def _on_setup_complete(self):
        """Called when setup wizard completes successfully"""
        self.logger.info("Setup completed - initializing application")
        
        # Schedule the continuation of initialization in the asyncio loop
        if self.event_loop:
            asyncio.create_task(self._continue_initialization_after_setup())
        else:
            # If no event loop yet, we'll handle this in the start() method
            self.logger.info("No event loop available yet - initialization will continue in start()")
    
    async def _continue_initialization_after_setup(self):
        """Continue initialization after setup wizard completion"""
        try:
            # Load the newly created configuration
            self.config = self.config_manager.load_config()
            
            # Apply theme
            self._apply_theme()
            
            # Initialize services
            await self._initialize_services()
            
            self.logger.info("Post-setup initialization completed successfully")
            
            # Start the application if we have all required components
            if not self.running:
                await self.start()
                
        except Exception as e:
            self.logger.error(f"Failed to continue initialization after setup: {e}")
            print(f"Error after setup: {e}")
    
    def _initialize_ui_root(self):
        """Initialize the root Tkinter window (hidden)"""
        try:
            # Create invisible root window for CustomTkinter
            self.root_window = ctk.CTk()
            self.root_window.withdraw()  # Hide the window
            
            # Configure default color theme only (appearance mode will be set after config load)
            ctk.set_default_color_theme("blue")
            
        except Exception as e:
            raise WindVoiceError(f"Failed to initialize UI root: {e}")
    
    def _apply_theme(self):
        """Apply the theme from configuration"""
        try:
            if self.config and self.config.ui:
                ctk.set_appearance_mode(self.config.ui.theme)
                self.logger.info(f"Theme set to: {self.config.ui.theme}")
            else:
                # Fallback to dark theme
                ctk.set_appearance_mode("dark")
                self.logger.warning("No config found, using default dark theme")
        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
            ctk.set_appearance_mode("dark")
    
    async def _initialize_services(self):
        self.logger.info("Starting service initialization...")
        
        # Audio recorder
        self.logger.info("Initializing AudioRecorder...")
        self.audio_recorder = AudioRecorder(
            sample_rate=self.config.app.sample_rate,
            device=self.config.app.audio_device
        )
        self.logger.info("AudioRecorder initialized successfully")
        
        # Transcription service with performance optimization
        self.logger.info("Initializing TranscriptionService...")
        self.transcription_service = TranscriptionService(self.config.litellm)
        
        # PERFORMANCE: Pre-warm HTTP connection for faster first transcription
        try:
            await self.transcription_service.warm_up_connection()
            self.logger.info("TranscriptionService initialized successfully with connection pre-warming")
        except Exception as e:
            self.logger.warning(f"TranscriptionService connection warm-up failed: {e}")
            self.logger.info("TranscriptionService initialized successfully (without pre-warming)")
        
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
        
        # If config is not loaded (because setup was needed), wait for setup completion
        if not self.config:
            self.logger.info("Configuration not loaded - waiting for setup completion")
            # Set event loop for setup completion callback
            self.event_loop = asyncio.get_event_loop()
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
                    f"Voice dictation is now running in the background. Press {self.config.app.hotkey} to start recording from any application."
                )
                
                # Show a secondary notification after a brief delay to confirm readiness
                async def show_ready_notification():
                    await asyncio.sleep(2.0)  # Wait 2 seconds
                    if self.running and self.system_tray:
                        self.system_tray.show_notification(
                            "WindVoice Ready",
                            "Voice dictation is ready and listening for hotkey activation."
                        )
                
                # Schedule the ready notification
                asyncio.create_task(show_ready_notification())
            
            print(f"WindVoice is now running in the background. Press {self.config.app.hotkey} to start recording from any application.")
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
                    except tk.TclError as tcl_error:
                        # Window was destroyed
                        self.logger.warning(f"Root window was destroyed - stopping app: {tcl_error}")
                        break
                    except Exception as tk_error:
                        # Other Tkinter errors - log but don't stop the app
                        self.logger.error(f"Tkinter update error (non-fatal): {tk_error}")
                        continue
                        
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
            
        except AudioDeviceBusyError as e:
            self.logger.error(f"AudioDeviceBusyError in _start_recording: {e}")
            self.recording = False
            self.system_tray.set_recording_state(False)
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            
            # Show specific tray notification for device busy
            self._show_device_busy_notification()
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Recording_Start_DEVICE_BUSY",
                {"error": str(e)}
            )
        except AudioError as e:
            self.logger.error(f"AudioError in _start_recording: {e}")
            self.recording = False
            self.system_tray.set_recording_state(False)
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            
            # Show specific tray notification for audio error
            self._show_audio_error_notification(str(e))
            
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
            
            # Show general error notification
            self._show_recording_error_notification(str(e))
            
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
            
            # PERFORMANCE OPTIMIZATION: Single audio validation call
            self.logger.info("Starting optimized audio validation...")
            quality_metrics = self.audio_recorder.get_quality_metrics(audio_file_path)
            
            # Get validation message from metrics (no additional file read)
            if not quality_metrics.has_voice:
                if quality_metrics.rms_level < 0.005:
                    title, message = "No Voice Detected", "Your recording appears to be silent or too quiet. Please try again and speak clearly into your microphone."
                else:
                    title, message = "Audio Quality Low", "Voice detection failed due to low audio quality. Please try recording in a quieter environment."
            else:
                title, message = "Audio Valid", f"Voice detected with quality score: {quality_metrics.quality_score:.2f}"
            
            WindVoiceLogger.log_audio_workflow_step(
                self.logger,
                "Audio_Validation_Complete_OPTIMIZED",
                {
                    "has_voice": quality_metrics.has_voice,
                    "quality_score": quality_metrics.quality_score,
                    "rms_level": quality_metrics.rms_level,
                    "duration": quality_metrics.duration,
                    "single_validation": True
                }
            )
            
            if not quality_metrics.has_voice:
                self.logger.info(f"No voice detected - showing error state")
                if self.root_window:
                    self.root_window.after(0, self.status_dialog.show_error)
                
                # Show tray notification for no voice detected
                self._show_no_voice_notification()
                
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
                
                # Show tray notification for failed transcription
                self._show_transcription_failed_notification()
                
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
            try:
                self.logger.info("Starting transcription result handling...")
                await self._handle_transcription_result(transcribed_text)
                self.logger.info("Transcription result handling completed successfully")
            except Exception as result_error:
                self.logger.error(f"Error handling transcription result: {result_error}")
                # Don't let this error propagate - just notify
                self._show_smart_notification(
                    "Transcription Error",
                    f"Error handling transcription: '{transcribed_text[:50]}{'...' if len(transcribed_text) > 50 else ''}'. Text available but display failed.",
                    is_error=True
                )
            
        except AudioError as e:
            self.logger.error(f"AudioError in _stop_recording: {e}")
            await self._cleanup_recording_state()
            if self.root_window:
                self.root_window.after(0, self.status_dialog.show_error)
            
            # Show tray notification for audio error
            self._show_audio_error_notification(str(e))
            
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
            
            # Show tray notification for transcription error
            self._show_transcription_error_notification(str(e))
            
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
            
            # Show tray notification for general error
            self._show_recording_error_notification(str(e))
            
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
        self.logger.info(f"Handling transcription result for text: '{text[:30]}{'...' if len(text) > 30 else ''}'")
        popup_created = False
        
        try:
            # Try to inject text directly
            self.logger.info("Attempting text injection...")
            success = self.text_injection_service.inject_text(text)
            self.logger.info(f"Text injection result: {success}")
            
            if success:
                # Show success animation and auto-close
                self.logger.info("Injection succeeded - showing success animation")
                if self.root_window:
                    self.root_window.after(0, self.status_dialog.show_success)
                else:
                    self.logger.warning("Root window not available for success animation")
            else:
                # Hide status dialog and show smart popup for text copy
                self.logger.info("Injection failed - showing popup dialog")
                if self.root_window:
                    self.root_window.after(0, self.status_dialog.hide)
                    # Schedule popup creation in the main thread
                    self.root_window.after(100, lambda: self._show_smart_popup_safely(text, "injection_failed"))
                    popup_created = True
                else:
                    self.logger.error("Cannot show popup: root window not available")
                    # Fallback to notification only (no clipboard copy)
                    self._show_smart_notification(
                        "Text Ready",
                        f"Transcription completed: '{text[:50]}{'...' if len(text) > 50 else ''}'. Use the popup to copy if needed.",
                        is_error=False
                    )
                
        except Exception as e:
            self.logger.error(f"Exception in _handle_transcription_result: {e}")
            # Only show error popup if we haven't already created one
            if not popup_created and self.root_window:
                try:
                    self.root_window.after(0, self.status_dialog.show_error)
                    # Schedule popup after error display
                    self.root_window.after(1000, lambda: self._show_smart_popup_safely(text, "injection_error"))
                    popup_created = True
                except Exception as ui_error:
                    self.logger.error(f"UI error handling failed: {ui_error}")
            
            # Final fallback only if no popup was created
            if not popup_created:
                self._show_smart_notification(
                    "Error",
                    f"Transcription completed but display failed: '{text[:30]}{'...' if len(text) > 30 else ''}'",
                    is_error=True
                )
                
        self.logger.info("_handle_transcription_result completed")
    
    def _show_injection_error_popup(self, text: str):
        """Helper method to show injection error popup"""
        self.status_dialog.hide()
        self.current_popup = show_smart_popup(
            text, 
            context="injection_error",
            timeout=20
        )
    
    def _show_smart_popup_safely(self, text: str, context: str):
        """Safely show smart popup with error handling"""
        try:
            self.logger.info(f"Creating smart popup for text: '{text[:50]}{'...' if len(text) > 50 else ''}' with context: {context}")
            self.current_popup = show_smart_popup(
                text, 
                context=context,
                parent_window=self.root_window
            )
            self.logger.info("Smart popup created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create smart popup: {e}")
            # Fallback: just show notification (no automatic clipboard copy)
            self._show_smart_notification(
                "Popup Error", 
                f"Could not open popup. Transcription: '{text[:50]}{'...' if len(text) > 50 else ''}'",
                is_error=True
            )
    
    def _show_smart_notification(self, title: str, message: str, is_error: bool = False):
        """Show intelligent notifications with better formatting"""
        self.logger.info(f"[NOTIFICATION] Attempting to show notification: '{title}' - '{message}' (error: {is_error})")
        
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
            
            self.logger.info(f"[NOTIFICATION] Calling system_tray.show_notification with: '{display_title}' - '{message}'")
            self.system_tray.show_notification(display_title, message)
            self.logger.info(f"[NOTIFICATION] System tray notification call completed")
        else:
            self.logger.error(f"[NOTIFICATION] System tray is not available!")
            
        # Also log with appropriate level
        log_level = "ERROR" if is_error else "INFO"
        print(f"{log_level} - {title}: {message}")
    
    def _show_error_notification(self, title: str, message: str):
        """Legacy method - redirects to smart notifications"""
        self._show_smart_notification(title, message, is_error=True)
    
    def _show_info_notification(self, title: str, message: str):
        """Legacy method - redirects to smart notifications"""
        self._show_smart_notification(title, message, is_error=False)
    
    def _show_device_busy_notification(self):
        """Show specific notification for busy audio device"""
        title = "Microphone In Use"
        message = "Your microphone is currently being used by another application (Teams, Zoom, etc.). Please close the other application or select a different audio device in Settings."
        self._show_smart_notification(title, message, is_error=True)
    
    def _show_audio_error_notification(self, error_message: str):
        """Show specific notification for audio errors"""
        title = "Audio Error"
        if "device" in error_message.lower() or "microphone" in error_message.lower():
            message = "There was a problem with your microphone. Please check your audio device settings or try selecting a different microphone in Settings."
        elif "permission" in error_message.lower() or "access" in error_message.lower():
            message = "WindVoice doesn't have permission to access your microphone. Please check your Windows privacy settings for microphone access."
        else:
            message = f"Audio recording failed: {error_message[:100]}{'...' if len(error_message) > 100 else ''}"
        self._show_smart_notification(title, message, is_error=True)
    
    def _show_transcription_error_notification(self, error_message: str):
        """Show specific notification for transcription errors"""
        title = "Transcription Error"
        if "api" in error_message.lower() or "key" in error_message.lower():
            message = "Unable to transcribe audio due to API configuration issues. Please check your LiteLLM settings in the Settings window."
        elif "network" in error_message.lower() or "connection" in error_message.lower():
            message = "Network connection error during transcription. Please check your internet connection and try again."
        elif "timeout" in error_message.lower():
            message = "Transcription service timed out. Please try again with a shorter recording."
        else:
            message = f"Failed to transcribe your recording. Please try again or check Settings for configuration issues."
        self._show_smart_notification(title, message, is_error=True)
    
    def _show_recording_error_notification(self, error_message: str):
        """Show specific notification for general recording errors"""
        title = "Recording Error"
        message = f"An unexpected error occurred while recording. Please try again. If the problem persists, check Settings or restart the application."
        self._show_smart_notification(title, message, is_error=True)
    
    def _show_no_voice_notification(self):
        """Show specific notification when no voice is detected in recording"""
        title = "No Voice Detected"
        message = "Your recording appears to be silent or too quiet. Please try again and speak clearly into your microphone."
        self._show_smart_notification(title, message, is_error=True)
    
    def _show_transcription_failed_notification(self):
        """Show specific notification when transcription returns empty result"""
        title = "Transcription Failed"
        message = "Unable to transcribe your recording. The audio may be unclear or the transcription service may be unavailable. Please try again."
        self._show_smart_notification(title, message, is_error=True)
    
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