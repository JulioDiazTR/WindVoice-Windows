"""
WindVoice Settings Window

Modern configuration interface with CustomTkinter for WindVoice settings,
including LiteLLM API configuration, audio device selection, and diagnostics.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Callable
import threading
import tempfile

from ..core.config import ConfigManager, WindVoiceConfig
from ..core.exceptions import ConfigurationError, AudioError
from ..services.audio import AudioRecorder
from ..services.transcription import TranscriptionService
from ..utils.logging import get_logger, WindVoiceLogger


class SettingsWindow:
    def __init__(self, config_manager: ConfigManager, audio_recorder: Optional[AudioRecorder] = None):
        self.logger = get_logger("settings")
        self.logger.info("Settings window initializing...")
        
        self.config_manager = config_manager
        self.audio_recorder = audio_recorder
        self.config = config_manager.load_config()
        
        # Window setup
        self.window = None
        self.is_visible = False
        
        self.logger.info("Settings window initialized successfully")
        
        # Form variables (will be created when window is created)
        self.api_key_var = None
        self.api_base_var = None
        self.key_alias_var = None
        self.hotkey_var = None
        self.audio_device_var = None
        self.sample_rate_var = None
        self.theme_var = None
        self.notifications_var = None
        
        # Audio testing
        self.available_devices: List[Dict] = []
        self.testing_audio = False
        
        # Diagnostic variables
        self.temp_folder_path = Path(tempfile.gettempdir()) / "windvoice"
        
        # Thread-safe communication variables
        self._test_result = None  # Will store {'status': 'success/error/testing', 'message': '...'}
        self._test_polling = False
        self._timeout_id = None
        
    def show(self):
        """Show the settings window"""
        self.logger.info("[UI] Settings window show() called")
        
        if self.window and self.is_visible:
            self.logger.info("[UI] Settings window already visible - bringing to front")
            self.window.lift()
            self.window.focus_force()
            return
            
        self.logger.info("[UI] Creating settings window...")
        self._create_window()
        
        self.logger.info("[UI] Loading current settings...")
        self._load_current_settings()
        
        self.is_visible = True
        self.logger.info("[UI] Settings window displayed successfully")
        
    def hide(self):
        """Hide the settings window"""
        if self.window:
            self.window.withdraw()
            self.is_visible = False
    
    def _create_window(self):
        """Create the main settings window"""
        # Initialize Tkinter variables here (after root window exists)
        self.api_key_var = ctk.StringVar()
        self.api_base_var = ctk.StringVar()
        self.key_alias_var = ctk.StringVar()
        self.hotkey_var = ctk.StringVar()
        self.audio_device_var = ctk.StringVar()
        self.sample_rate_var = ctk.StringVar()
        self.theme_var = ctk.StringVar()
        self.notifications_var = ctk.BooleanVar()
        
        self.window = ctk.CTkToplevel()
        self.window.title("WindVoice Settings")
        self.window.geometry("700x800")
        self.window.resizable(True, True)
        
        # Configure theme from config
        ctk.set_appearance_mode(self.config.ui.theme)
        ctk.set_default_color_theme("blue")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.window.winfo_screenheight() // 2) - (800 // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Window close handler
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Create scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame, 
            text="WindVoice Configuration",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create sections
        self._create_litellm_section()
        self._create_audio_section()
        self._create_hotkey_section()
        self._create_ui_section()
        self._create_diagnostics_section()
        self._create_action_buttons()
        
    def _create_litellm_section(self):
        """Create LiteLLM API configuration section"""
        # Section frame
        litellm_frame = ctk.CTkFrame(self.main_frame)
        litellm_frame.pack(fill="x", pady=(0, 20))
        
        # Section title
        title = ctk.CTkLabel(
            litellm_frame,
            text="🤖 Thomson Reuters LiteLLM Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(15, 10))
        
        # API Key
        ctk.CTkLabel(litellm_frame, text="API Key:").pack(anchor="w", padx=20)
        self.api_key_entry = ctk.CTkEntry(
            litellm_frame,
            textvariable=self.api_key_var,
            placeholder_text="sk-your-api-key-here",
            show="*",
            width=400
        )
        self.api_key_entry.pack(pady=(5, 10), padx=20, fill="x")
        
        # API Base URL
        ctk.CTkLabel(litellm_frame, text="API Base URL:").pack(anchor="w", padx=20)
        self.api_base_entry = ctk.CTkEntry(
            litellm_frame,
            textvariable=self.api_base_var,
            placeholder_text="https://your-litellm-proxy.com",
            width=400
        )
        self.api_base_entry.pack(pady=(5, 10), padx=20, fill="x")
        
        # Key Alias
        ctk.CTkLabel(litellm_frame, text="Key Alias (User ID):").pack(anchor="w", padx=20)
        self.key_alias_entry = ctk.CTkEntry(
            litellm_frame,
            textvariable=self.key_alias_var,
            placeholder_text="your-username",
            width=400
        )
        self.key_alias_entry.pack(pady=(5, 10), padx=20, fill="x")
        
        # Test API button
        self.test_api_button = ctk.CTkButton(
            litellm_frame,
            text="🔍 Test API Connection",
            command=self._test_api_connection,
            width=200
        )
        self.test_api_button.pack(pady=(10, 15))
        
    def _create_audio_section(self):
        """Create audio configuration section"""
        # Section frame
        audio_frame = ctk.CTkFrame(self.main_frame)
        audio_frame.pack(fill="x", pady=(0, 20))
        
        # Section title
        title = ctk.CTkLabel(
            audio_frame,
            text="🎤 Audio Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(15, 10))
        
        # Audio device selection
        ctk.CTkLabel(audio_frame, text="Audio Device:").pack(anchor="w", padx=20)
        self.audio_device_combo = ctk.CTkComboBox(
            audio_frame,
            variable=self.audio_device_var,
            values=["Loading devices..."],
            width=400
        )
        self.audio_device_combo.pack(pady=(5, 10), padx=20, fill="x")
        
        # Refresh devices button
        refresh_button = ctk.CTkButton(
            audio_frame,
            text="🔄 Refresh Devices",
            command=self._refresh_audio_devices,
            width=150
        )
        refresh_button.pack(pady=(0, 10))
        
        # Sample rate
        ctk.CTkLabel(audio_frame, text="Sample Rate:").pack(anchor="w", padx=20)
        self.sample_rate_combo = ctk.CTkComboBox(
            audio_frame,
            variable=self.sample_rate_var,
            values=["44100", "48000", "22050", "16000"],
            width=200
        )
        self.sample_rate_combo.pack(pady=(5, 10), padx=20, anchor="w")
        
        # Test microphone button
        self.test_mic_button = ctk.CTkButton(
            audio_frame,
            text="🎙️ Test Microphone",
            command=self._test_microphone,
            width=200
        )
        self.test_mic_button.pack(pady=(10, 15))
        
    def _create_hotkey_section(self):
        """Create hotkey configuration section"""
        # Section frame
        hotkey_frame = ctk.CTkFrame(self.main_frame)
        hotkey_frame.pack(fill="x", pady=(0, 20))
        
        # Section title
        title = ctk.CTkLabel(
            hotkey_frame,
            text="⌨️ Hotkey Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(15, 10))
        
        # Hotkey selection
        ctk.CTkLabel(hotkey_frame, text="Recording Hotkey:").pack(anchor="w", padx=20)
        self.hotkey_combo = ctk.CTkComboBox(
            hotkey_frame,
            variable=self.hotkey_var,
            values=[
                "ctrl+shift+space",
                "ctrl+alt+space",
                "ctrl+shift+v",
                "alt+shift+space",
                "ctrl+shift+r"
            ],
            width=300
        )
        self.hotkey_combo.pack(pady=(5, 15), padx=20, anchor="w")
        
    def _create_ui_section(self):
        """Create UI preferences section"""
        # Section frame
        ui_frame = ctk.CTkFrame(self.main_frame)
        ui_frame.pack(fill="x", pady=(0, 20))
        
        # Section title
        title = ctk.CTkLabel(
            ui_frame,
            text="🎨 Interface Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(15, 10))
        
        # Theme selection
        ctk.CTkLabel(ui_frame, text="Theme:").pack(anchor="w", padx=20)
        self.theme_combo = ctk.CTkComboBox(
            ui_frame,
            variable=self.theme_var,
            values=["dark", "light"],
            width=200,
            command=self._on_theme_change
        )
        self.theme_combo.pack(pady=(5, 10), padx=20, anchor="w")
        
        # Show notifications
        self.notifications_checkbox = ctk.CTkCheckBox(
            ui_frame,
            text="Show tray notifications",
            variable=self.notifications_var
        )
        self.notifications_checkbox.pack(pady=(10, 15), padx=20, anchor="w")
        
    def _create_diagnostics_section(self):
        """Create diagnostics and debugging section"""
        # Section frame
        diag_frame = ctk.CTkFrame(self.main_frame)
        diag_frame.pack(fill="x", pady=(0, 20))
        
        # Section title
        title = ctk.CTkLabel(
            diag_frame,
            text="🔧 Diagnostics & Debugging",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(15, 10))
        
        # Buttons row
        button_frame = ctk.CTkFrame(diag_frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        # Open audio folder button
        self.open_folder_button = ctk.CTkButton(
            button_frame,
            text="📁 Open Audio Folder",
            command=self._open_audio_folder,
            width=180
        )
        self.open_folder_button.pack(side="left", padx=(0, 10), pady=10)
        
        # Clear temp files button
        self.clear_temp_button = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear Temp Files",
            command=self._clear_temp_files,
            width=180
        )
        self.clear_temp_button.pack(side="left", padx=10, pady=10)
        
        # Show config file button
        self.show_config_button = ctk.CTkButton(
            button_frame,
            text="📄 Show Config File",
            command=self._show_config_file,
            width=180
        )
        self.show_config_button.pack(side="left", padx=10, pady=10)
        
        # Status text
        self.status_text = ctk.CTkTextbox(
            diag_frame,
            height=100,
            width=600
        )
        self.status_text.pack(pady=(10, 15), padx=20, fill="x")
        
        self._update_diagnostics_status()
        
    def _create_action_buttons(self):
        """Create action buttons (Save, Cancel, etc.)"""
        # Button frame
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=20)
        
        # Buttons
        save_button = ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self._save_settings,
            width=150
        )
        save_button.pack(side="left", padx=(20, 10), pady=15)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self._cancel_settings,
            width=150
        )
        cancel_button.pack(side="left", padx=10, pady=15)
        
        reset_button = ctk.CTkButton(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self._reset_to_defaults,
            width=150
        )
        reset_button.pack(side="right", padx=(10, 20), pady=15)
        
    def _load_current_settings(self):
        """Load current configuration into form"""
        # LiteLLM settings
        self.api_key_var.set(self.config.litellm.api_key or "")
        self.api_base_var.set(self.config.litellm.api_base or "")
        self.key_alias_var.set(self.config.litellm.key_alias or "")
        
        # App settings
        self.hotkey_var.set(self.config.app.hotkey)
        self.audio_device_var.set(self.config.app.audio_device)
        self.sample_rate_var.set(str(self.config.app.sample_rate))
        
        # UI settings
        self.theme_var.set(self.config.ui.theme)
        self.notifications_var.set(self.config.ui.show_tray_notifications)
        
        # Load audio devices
        self._refresh_audio_devices()
        
    def _refresh_audio_devices(self):
        """Refresh the list of available audio devices"""
        try:
            if not self.audio_recorder:
                self.audio_recorder = AudioRecorder()
                
            self.available_devices = self.audio_recorder.get_available_devices()
            device_names = ["default"] + [f"{dev['name']} (ID: {dev['index']})" for dev in self.available_devices]
            
            self.audio_device_combo.configure(values=device_names)
            
            # Set current device
            current_device = self.config.app.audio_device
            if current_device in device_names:
                self.audio_device_var.set(current_device)
            else:
                self.audio_device_var.set("default")
                
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to load audio devices: {e}")
            
    def _test_api_connection(self):
        """Test the LiteLLM API connection"""
        self.logger.info("[UI] LiteLLM test button clicked")
        
        # Read all values in main thread BEFORE starting background thread
        try:
            api_key = self.api_key_var.get() if self.api_key_var else ""
            api_base = self.api_base_var.get() if self.api_base_var else ""
            key_alias = self.key_alias_var.get() if self.key_alias_var else ""
        except Exception as e:
            self.logger.error(f"[UI] Failed to read API configuration: {e}")
            messagebox.showerror("UI Error", f"Failed to read configuration: {e}")
            return
        
        self.logger.info(f"[UI] Test values - API Base: {api_base}, Key Alias: {key_alias}, API Key: {'***' if api_key else 'EMPTY'}")
        
        if not all([api_key, api_base, key_alias]):
            self.logger.warning("[UI] Missing API configuration fields")
            messagebox.showwarning("Missing Information", "Please fill in all LiteLLM API fields before testing.")
            return
            
        self.logger.info("[UI] Starting API test - changing button to Testing...")
        self.test_api_button.configure(text="Testing...", state="disabled")
        
        # Store values for the background thread
        self._test_config = {
            'api_key': api_key,
            'api_base': api_base,
            'key_alias': key_alias
        }
        
        # Initialize test result and start polling
        self._test_result = {'status': 'testing', 'message': 'Test in progress...'}
        self._test_polling = True
        
        # Start polling for results (every 250ms)
        self._poll_test_result()
        
        # Add timeout fallback in case thread fails
        self._timeout_id = self.window.after(15000, self._test_timeout_fallback)  # 15 second timeout
        
        # Run test in background thread
        self.logger.info("[UI] Starting background thread for API test")
        thread = threading.Thread(target=self._run_api_test, daemon=True)
        thread.start()
        self.logger.info("[UI] Background thread started")
        
    def _run_api_test(self):
        """Run API test in background thread"""
        import asyncio
        
        self.logger.info("[THREAD] _run_api_test started in background thread")
        
        try:
            # Use pre-stored configuration from main thread
            if not hasattr(self, '_test_config') or not self._test_config:
                self.logger.error("[THREAD] No test configuration available")
                self._test_result = {'status': 'error', 'message': 'No configuration available for test'}
                return
            
            api_key = self._test_config['api_key']
            api_base = self._test_config['api_base'] 
            key_alias = self._test_config['key_alias']
            
            self.logger.info(f"[THREAD] Using stored config - API Base: {api_base}, Key Alias: {key_alias}, API Key present: {bool(api_key)}")
            
            if not all([api_key, api_base, key_alias]):
                self.logger.error(f"[THREAD] Missing required fields - API Key: {bool(api_key)}, API Base: {bool(api_base)}, Key Alias: {bool(key_alias)}")
                self._test_result = {'status': 'error', 'message': 'Missing required configuration fields'}
                return
            
            print(f"\n[LITELLM TEST] Starting connection test...")
            print(f"API Base: {api_base}")
            print(f"Key Alias: {key_alias}")
            print(f"API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '[REDACTED]'}")
            print("-" * 60)
            
            self.logger.info("[THREAD] Creating LiteLLM config for testing...")
            
            # Create temporary config for testing
            from ..core.config import LiteLLMConfig
            test_config = LiteLLMConfig(
                api_key=api_key,
                api_base=api_base,
                key_alias=key_alias,
                model="whisper-1"
            )
            
            self.logger.info("[THREAD] Creating TranscriptionService...")
            test_service = TranscriptionService(test_config)
            
            # Run the async test
            try:
                self.logger.info("[THREAD] Setting up asyncio event loop...")
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                self.logger.info("[THREAD] Running async test_connection()...")
                success, message = loop.run_until_complete(test_service.test_connection())
                
                self.logger.info(f"[THREAD] Test completed - Success: {success}, Message: {message}")
                
                # Clean up
                self.logger.info("[THREAD] Cleaning up async resources...")
                loop.run_until_complete(test_service.close())
                loop.close()
                
                print(f"\n[TEST RESULT] {'SUCCESS' if success else 'FAILED'}")
                print(f"Message: {message}")
                print("-" * 60)
                
                if success:
                    self.logger.info("[THREAD] Test succeeded - updating result")
                    self._test_result = {'status': 'success', 'message': message}
                else:
                    self.logger.info("[THREAD] Test failed - updating result")
                    self._test_result = {'status': 'error', 'message': message}
                    
            except Exception as e:
                error_msg = f"Test execution failed: {str(e)}"
                self.logger.error(f"[THREAD] Test execution error: {e}")
                print(f"[ERROR] {error_msg}")
                self._test_result = {'status': 'error', 'message': error_msg}
            
        except Exception as e:
            error_msg = f"Test setup failed: {str(e)}"
            self.logger.error(f"[THREAD] Test setup error: {e}")
            print(f"[ERROR] {error_msg}")
            self._test_result = {'status': 'error', 'message': error_msg}
        
        self.logger.info("[THREAD] _run_api_test completed")
    
    def _poll_test_result(self):
        """Poll for test results from main thread - this can safely update UI"""
        if not self._test_polling:
            return
        
        try:
            if self._test_result and self._test_result['status'] != 'testing':
                # Test completed - process result
                result = self._test_result
                status = result['status'] 
                message = result['message']
                
                self.logger.info(f"[POLL] Test completed with status: {status}, message: {message}")
                
                # Stop polling
                self._test_polling = False
                
                # Cancel timeout
                self._cancel_timeout()
                
                # Update UI based on result
                if status == 'success':
                    self._handle_test_success(message)
                elif status == 'error':
                    self._handle_test_error(message)
                
                # Clear result
                self._test_result = None
                
            else:
                # Test still in progress - continue polling
                self.window.after(250, self._poll_test_result)  # Poll every 250ms
                
        except Exception as e:
            self.logger.error(f"[POLL] Error during polling: {e}")
            # Stop polling on error
            self._test_polling = False
    
    def _handle_test_success(self, message: str):
        """Handle successful test result in main thread"""
        self.logger.info(f"[UI] Handling test success: {message}")
        
        try:
            self.test_api_button.configure(text="Connection OK", state="normal")
            print(f"[SUCCESS] LiteLLM Test Success: {message}")
            messagebox.showinfo("API Test Successful", f"LiteLLM connection test passed!\n\n{message}")
            
            # Reset button after 3 seconds
            self.window.after(3000, self._reset_test_button)
            
        except Exception as e:
            self.logger.error(f"[UI] Error handling success: {e}")
    
    def _handle_test_error(self, message: str):
        """Handle failed test result in main thread"""
        self.logger.info(f"[UI] Handling test error: {message}")
        
        try:
            self.test_api_button.configure(text="Test Failed", state="normal")
            print(f"[ERROR] LiteLLM Test Failed: {message}")
            messagebox.showerror("API Test Failed", f"LiteLLM connection test failed:\n\n{message}\n\nCheck the console for detailed logs.")
            
            # Reset button after 5 seconds (longer for errors)
            self.window.after(5000, self._reset_test_button)
            
        except Exception as e:
            self.logger.error(f"[UI] Error handling error: {e}")
    
    def _schedule_ui_update(self, callback, *args):
        """Safely schedule UI update from background thread"""
        self.logger.info(f"[THREAD] Scheduling UI update - callback: {callback.__name__}, args: {args}")
        
        try:
            if self.window and self.window.winfo_exists():
                self.logger.info("[THREAD] Window exists - scheduling callback")
                if args:
                    self.window.after(0, lambda: callback(*args))
                else:
                    self.window.after(0, callback)
                self.logger.info("[THREAD] UI update scheduled successfully")
            else:
                self.logger.warning("[THREAD] Window does not exist or was destroyed")
        except (RuntimeError, tk.TclError) as e:
            self.logger.error(f"[THREAD] Failed to schedule UI update: {e}")
        except Exception as e:
            self.logger.error(f"[THREAD] Unexpected error in _schedule_ui_update: {e}")
    
    def _safe_ui_update_print(self, message: str):
        """Print message and try basic console feedback when UI update fails"""
        print(f"[UI UPDATE] {message}")
        self.logger.info(f"[THREAD] Safe print: {message}")
    
    def _safe_ui_update_success(self, message: str):
        """Safely update UI for success, with print fallback"""
        try:
            self._schedule_ui_update(self._on_api_test_success, message)
        except Exception as e:
            self.logger.error(f"[THREAD] UI update failed, using print fallback: {e}")
            print(f"[SUCCESS] LiteLLM Test Passed: {message}")
            print("[INFO] Please manually reset the test button if it's stuck")
    
    def _safe_ui_update_error(self, message: str):
        """Safely update UI for error, with print fallback"""
        try:
            self._schedule_ui_update(self._on_api_test_error, message)
        except Exception as e:
            self.logger.error(f"[THREAD] UI update failed, using print fallback: {e}")
            print(f"[ERROR] LiteLLM Test Failed: {message}")
            print("[INFO] Please manually reset the test button if it's stuck")
    
    def _test_timeout_fallback(self):
        """Fallback to reset button if test takes too long"""
        try:
            if self._test_polling and self._test_result and self._test_result['status'] == 'testing':
                self.logger.warning("[UI] Test timeout - stopping test")
                
                # Stop polling
                self._test_polling = False
                
                # Update button
                self.test_api_button.configure(text="Test Timeout", state="normal")
                print("[TIMEOUT] API test timed out after 15 seconds")
                
                # Show error dialog
                messagebox.showerror("Test Timeout", "The API connection test timed out.\n\nThis may indicate network issues or server problems.")
                
                # Reset after showing timeout
                self.window.after(2000, self._reset_test_button)
                
                # Clear result
                self._test_result = None
                
        except Exception as e:
            self.logger.error(f"[UI] Error in timeout fallback: {e}")
            
    def _on_api_test_success(self, message: str = "Connection successful"):
        """Handle successful API test"""
        self.logger.info(f"[UI] _on_api_test_success called with message: {message}")
        
        # Cancel timeout since test completed
        self._cancel_timeout()
        
        try:
            self.test_api_button.configure(text="Connection OK", state="normal")
            self.logger.info("[UI] Button updated to success state")
            
            print(f"[SUCCESS] LiteLLM Test Success: {message}")
            
            messagebox.showinfo("API Test Successful", f"LiteLLM connection test passed!\n\n{message}")
            self.logger.info("[UI] Success dialog shown")
            
            # Reset button after 3 seconds
            self.window.after(3000, lambda: self._reset_test_button())
            self.logger.info("[UI] Button reset scheduled")
            
        except Exception as e:
            self.logger.error(f"[UI] Error in _on_api_test_success: {e}")
        
    def _on_api_test_error(self, error_message: str):
        """Handle failed API test"""
        self.logger.info(f"[UI] _on_api_test_error called with message: {error_message}")
        
        # Cancel timeout since test completed
        self._cancel_timeout()
        
        try:
            self.test_api_button.configure(text="Test Failed", state="normal")
            self.logger.info("[UI] Button updated to error state")
            
            print(f"[FAILED] LiteLLM Test Failed: {error_message}")
            
            messagebox.showerror("API Test Failed", f"LiteLLM connection test failed:\n\n{error_message}\n\nCheck the console for detailed logs.")
            self.logger.info("[UI] Error dialog shown")
            
            # Reset button after 3 seconds
            self.window.after(3000, lambda: self._reset_test_button())
            self.logger.info("[UI] Button reset scheduled")
            
        except Exception as e:
            self.logger.error(f"[UI] Error in _on_api_test_error: {e}")
    
    def _cancel_timeout(self):
        """Cancel the timeout timer"""
        try:
            if hasattr(self, '_timeout_id') and self._timeout_id:
                self.window.after_cancel(self._timeout_id)
                self._timeout_id = None
                self.logger.info("[UI] Test timeout cancelled")
        except Exception as e:
            self.logger.error(f"[UI] Error cancelling timeout: {e}")
    
    def _reset_test_button(self):
        """Reset the test button to original state"""
        try:
            self.test_api_button.configure(text="Test API Connection", state="normal")
            self.logger.info("[UI] Test button reset to original state")
        except Exception as e:
            self.logger.error(f"[UI] Error resetting test button: {e}")
        
    def _test_microphone(self):
        """Test the selected microphone"""
        if self.testing_audio:
            return
            
        try:
            self.testing_audio = True
            self.test_mic_button.configure(text="🔄 Testing...", state="disabled")
            
            # Test the microphone
            device_name = self.audio_device_var.get()
            device_index = None
            
            if device_name != "default":
                # Find device index
                for dev in self.available_devices:
                    if f"{dev['name']} (ID: {dev['index']})" == device_name:
                        device_index = dev['index']
                        break
                        
            success = self.audio_recorder.test_device(device_index)
            
            if success:
                self.test_mic_button.configure(text="✅ Microphone OK")
                self.window.after(3000, lambda: self._reset_mic_test_button())
            else:
                self.test_mic_button.configure(text="❌ Test Failed")
                messagebox.showerror("Microphone Test", "Microphone test failed. Please check your audio device.")
                self.window.after(3000, lambda: self._reset_mic_test_button())
                
        except Exception as e:
            self.test_mic_button.configure(text="❌ Error")
            messagebox.showerror("Microphone Error", f"Failed to test microphone: {e}")
            self.window.after(3000, lambda: self._reset_mic_test_button())
        finally:
            self.testing_audio = False
            
    def _reset_mic_test_button(self):
        """Reset microphone test button"""
        self.test_mic_button.configure(text="🎙️ Test Microphone", state="normal")
        
    def _open_audio_folder(self):
        """Open the temporary audio folder in file explorer"""
        try:
            # Ensure the folder exists
            self.temp_folder_path.mkdir(exist_ok=True)
            
            # Open in file explorer
            if sys.platform == "win32":
                os.startfile(str(self.temp_folder_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.temp_folder_path)])
            else:
                subprocess.run(["xdg-open", str(self.temp_folder_path)])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open audio folder: {e}")
            
    def _clear_temp_files(self):
        """Clear temporary audio files"""
        try:
            count = 0
            for file in self.temp_folder_path.glob("*.wav"):
                if file.exists():
                    file.unlink()
                    count += 1
                    
            messagebox.showinfo("Success", f"Cleared {count} temporary audio files.")
            self._update_diagnostics_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear temporary files: {e}")
            
    def _show_config_file(self):
        """Open the configuration file in default text editor"""
        try:
            config_path = self.config_manager.config_file_path
            
            if sys.platform == "win32":
                os.startfile(str(config_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(config_path)])
            else:
                subprocess.run(["xdg-open", str(config_path)])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open config file: {e}")
            
    def _update_diagnostics_status(self):
        """Update the diagnostics status display"""
        try:
            status_info = []
            
            # Config file status
            config_path = self.config_manager.config_file_path
            status_info.append(f"Config file: {config_path}")
            status_info.append(f"Config exists: {'Yes' if config_path.exists() else 'No'}")
            
            # Audio folder status
            status_info.append(f"Audio folder: {self.temp_folder_path}")
            status_info.append(f"Audio folder exists: {'Yes' if self.temp_folder_path.exists() else 'No'}")
            
            if self.temp_folder_path.exists():
                wav_files = list(self.temp_folder_path.glob("*.wav"))
                status_info.append(f"Temporary audio files: {len(wav_files)}")
                
            # API status
            has_api_config = all([
                self.config.litellm.api_key,
                self.config.litellm.api_base,
                self.config.litellm.key_alias
            ])
            status_info.append(f"LiteLLM configured: {'Yes' if has_api_config else 'No'}")
            
            # Update text widget
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "\n".join(status_info))
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error updating status: {e}")
            
    def _save_settings(self):
        """Save the current settings"""
        try:
            # Validate required fields
            if not all([self.api_key_var.get(), self.api_base_var.get(), self.key_alias_var.get()]):
                messagebox.showwarning("Missing Information", "Please fill in all LiteLLM API fields.")
                return
                
            # Update config object
            self.config.litellm.api_key = self.api_key_var.get().strip()
            self.config.litellm.api_base = self.api_base_var.get().strip()
            self.config.litellm.key_alias = self.key_alias_var.get().strip()
            
            self.config.app.hotkey = self.hotkey_var.get()
            self.config.app.audio_device = self.audio_device_var.get()
            self.config.app.sample_rate = int(self.sample_rate_var.get())
            
            self.config.ui.theme = self.theme_var.get()
            self.config.ui.show_tray_notifications = self.notifications_var.get()
            
            # Save configuration
            self.config_manager.save_config(self.config)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self._update_diagnostics_status()
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")
            
    def _cancel_settings(self):
        """Cancel changes and close window"""
        self.hide()
        
    def _reset_to_defaults(self):
        """Reset settings to default values"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            try:
                # Create default config
                default_config = WindVoiceConfig()
                
                # Load defaults into form (except API keys)
                self.hotkey_var.set(default_config.app.hotkey)
                self.audio_device_var.set(default_config.app.audio_device)
                self.sample_rate_var.set(str(default_config.app.sample_rate))
                self.theme_var.set(default_config.ui.theme)
                self.notifications_var.set(default_config.ui.show_tray_notifications)
                
                messagebox.showinfo("Reset Complete", "Settings have been reset to defaults. Click 'Save Settings' to apply.")
                
            except Exception as e:
                messagebox.showerror("Reset Error", f"Failed to reset settings: {e}")
                
    def _on_theme_change(self, value):
        """Handle theme change immediately"""
        try:
            self.logger.info(f"Theme changed to: {value}")
            ctk.set_appearance_mode(value)
        except Exception as e:
            self.logger.error(f"Error changing theme: {e}")
            
    def _on_close(self):
        """Handle window close event"""
        self.hide()


# Factory function for creating settings window
def create_settings_window(config_manager: ConfigManager, 
                         audio_recorder: Optional[AudioRecorder] = None) -> SettingsWindow:
    """Create a new settings window instance"""
    return SettingsWindow(config_manager, audio_recorder)