"""
WindVoice Setup Wizard

First-time setup wizard for new users to configure their LiteLLM API credentials
and basic application settings. This ensures clean installation without pre-existing
configuration.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Callable

from ..core.config import ConfigManager, WindVoiceConfig, LiteLLMConfig, AppConfig, UIConfig


class SetupWizard:
    def __init__(self, config_manager: ConfigManager, on_complete: Optional[Callable] = None):
        self.config_manager = config_manager
        self.on_complete = on_complete
        
        # Window setup
        self.window = None
        self.is_visible = False
        
        # Form variables
        self.api_key_var = None
        self.api_base_var = None
        self.key_alias_var = None
        self.theme_var = None
        self.notifications_var = None
        
        # Current step tracking
        self.current_step = 0
        self.total_steps = 3
        
    def show(self):
        """Show the setup wizard"""
        if self.window and self.is_visible:
            self.window.lift()
            self.window.focus_force()
            return
            
        self._create_window()
        self.is_visible = True
        
        # Make sure the window is visible
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        
        print("Setup wizard window created and showing...")
        print("Please complete the setup in the window that appeared.")
        
        # Keep the window updated without blocking
        self._run_window_loop()
        
    def hide(self):
        """Hide the setup wizard"""
        if self.window:
            self.window.withdraw()
            self.is_visible = False
    
    def _create_window(self):
        """Create the main setup window"""
        try:
            print("Creating setup window...")
            
            # Initialize CustomTkinter if not already done
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
            print("CustomTkinter configured, creating window...")
            
            # Create main window instead of toplevel for better reliability
            self.window = ctk.CTk()
            print("CTk window created")
            
            # Initialize variables after window creation
            self.api_key_var = ctk.StringVar()
            self.api_base_var = ctk.StringVar()
            self.key_alias_var = ctk.StringVar()
            self.theme_var = ctk.StringVar(value="dark")
            self.notifications_var = ctk.BooleanVar(value=True)
            print("Variables initialized")
            
            # Configure window
            self.window.title("WindVoice-Windows Setup - First Time Configuration")
            self.window.geometry("600x700")
            self.window.resizable(False, False)
            
            # Make window stay on top and focused
            self.window.attributes("-topmost", True)
            print("Window attributes set")
        
            # Center the window - do this after geometry is set
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
            y = (self.window.winfo_screenheight() // 2) - (700 // 2)
            self.window.geometry(f"600x700+{x}+{y}")
            print(f"Window centered at {x},{y}")
            
            # Prevent closing without completing setup
            self.window.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
            
            print("Setup window creation completed successfully")
            
        except Exception as e:
            print(f"Error creating setup window: {e}")
            import traceback
            traceback.print_exc()
            # Try a simpler approach - create basic window
            self._create_simple_window()
        
        # Create main container after window is fully initialized
        try:
            print("Creating main frame...")
            self.main_frame = ctk.CTkFrame(self.window)
            self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            print("Main frame created and packed")
            
            # Create the welcome step content
            print("Creating welcome step...")
            self._create_welcome_step()
            print("Welcome step created")
            
        except Exception as e:
            print(f"Error creating main frame: {e}")
            import traceback
            traceback.print_exc()
            
            # Show simple message if everything fails
            try:
                label = ctk.CTkLabel(self.window, text="Setup wizard failed to load properly.\nPlease close this window and check the console for manual setup instructions.", wraplength=500)
                label.pack(expand=True, pady=50)
            except:
                # Ultimate fallback
                import tkinter as tk
                label = tk.Label(self.window, text="Setup wizard failed to load properly.\nPlease close this window and check the console for manual setup instructions.", bg='white', wraplength=500)
                label.pack(expand=True, pady=50)
    
    def _create_simple_window(self):
        """Create a simpler window as fallback"""
        import tkinter as tk
        
        # Fall back to basic Tkinter if CustomTkinter fails
        self.window = tk.Tk()
        self.window.title("WindVoice-Windows Setup")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Make it stay on top
        self.window.attributes("-topmost", True)
        self.window.focus_force()
        
        # Prevent closing
        self.window.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
        
        print("Setup wizard created with basic Tkinter fallback")
    
    def _run_window_loop(self):
        """Show the window and let the main app handle the event loop"""
        # Don't run mainloop here - let the main app handle updates
        # Just make sure the window is visible and responsive
        try:
            print("Setup wizard window is ready - main app will handle updates")
            # The window should already be visible from show()
            # The main app's event loop will keep it responsive
        except Exception as e:
            print(f"Window setup error: {e}")
        
    def _create_welcome_step(self):
        """Create the welcome step"""
        try:
            print("Clearing previous content...")
            self._clear_content()
            self.current_step = 0
            
            print("Creating progress indicator...")
            # Progress indicator
            self._create_progress_indicator()
            
            print("Creating welcome label...")
            # Welcome content
            welcome_label = ctk.CTkLabel(
                self.main_frame,
                text="Welcome to WindVoice-Windows! 🎙️",
                font=ctk.CTkFont(size=28, weight="bold")
            )
            welcome_label.pack(pady=(40, 20))
            print("Welcome label created and packed")
            
            print("Creating description...")
            description = ctk.CTkLabel(
                self.main_frame,
                text="Fast and accurate voice-to-text transcription for Windows\\n\\n"
                     "This setup wizard will help you configure:\\n"
                     "• Thomson Reuters LiteLLM API credentials\\n"
                     "• Basic application preferences\\n"
                     "• Audio device settings\\n\\n"
                     "Let's get started!",
                font=ctk.CTkFont(size=14),
                justify="center"
            )
            description.pack(pady=20)
            
            print("Creating feature highlights...")
            # Feature highlights
            features_frame = ctk.CTkFrame(self.main_frame)
            features_frame.pack(fill="x", pady=30, padx=40)
            
            features_title = ctk.CTkLabel(
                features_frame,
                text="✨ Key Features",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            features_title.pack(pady=(15, 10))
            
            features_text = ctk.CTkLabel(
                features_frame,
                text="🔥 Global hotkey (Ctrl+Shift+Space) for instant recording\\n"
                     "⚡ Optimized for 2-3 second transcription performance\\n"
                     "🎯 Smart text injection into any Windows application\\n"
                     "🔒 Secure local configuration storage\\n"
                     "🎨 Modern, clean interface",
                font=ctk.CTkFont(size=12),
                justify="left"
            )
            features_text.pack(pady=(0, 15))
            
            print("Creating next button...")
            # Next button
            next_button = ctk.CTkButton(
                self.main_frame,
                text="Get Started →",
                command=self._create_api_step,
                font=ctk.CTkFont(size=14, weight="bold"),
                height=40,
                width=200
            )
            next_button.pack(pady=30)
            print("Welcome step creation completed successfully")
            
        except Exception as e:
            print(f"Error in _create_welcome_step: {e}")
            import traceback
            traceback.print_exc()
            # Create a simple fallback
            try:
                simple_label = ctk.CTkLabel(self.main_frame, text="WindVoice-Windows Setup", font=ctk.CTkFont(size=20))
                simple_label.pack(pady=50)
                simple_button = ctk.CTkButton(self.main_frame, text="Continue", command=self._create_api_step)
                simple_button.pack(pady=20)
            except Exception as e2:
                print(f"Even simple fallback failed: {e2}")
        
    def _create_api_step(self):
        """Create the API configuration step"""
        self._clear_content()
        self.current_step = 1
        
        # Progress indicator
        self._create_progress_indicator()
        
        # Step title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Thomson Reuters LiteLLM Setup",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Configure your AI transcription credentials",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Form frame
        form_frame = ctk.CTkFrame(self.main_frame)
        form_frame.pack(fill="x", padx=20, pady=10)
        
        # API Key
        ctk.CTkLabel(form_frame, text="API Key *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.api_key_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.api_key_var,
            placeholder_text="sk-your-virtual-api-key-here",
            show="*",
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.api_key_entry.pack(pady=(0, 10), padx=20, fill="x")
        
        # API Base URL
        ctk.CTkLabel(form_frame, text="API Base URL *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.api_base_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.api_base_var,
            placeholder_text="https://your-litellm-proxy.company.com",
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.api_base_entry.pack(pady=(0, 10), padx=20, fill="x")
        
        # Key Alias
        ctk.CTkLabel(form_frame, text="User ID / Key Alias *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.key_alias_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.key_alias_var,
            placeholder_text="your-username or employee-id",
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.key_alias_entry.pack(pady=(0, 20), padx=20, fill="x")
        
        # Help text
        help_text = ctk.CTkLabel(
            self.main_frame,
            text="💡 Contact your IT administrator for these credentials\\n"
                 "🔒 Your credentials are stored locally and securely",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="center"
        )
        help_text.pack(pady=15)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        back_button = ctk.CTkButton(
            button_frame,
            text="← Back",
            command=self._create_welcome_step,
            width=100
        )
        back_button.pack(side="left", padx=20, pady=10)
        
        next_button = ctk.CTkButton(
            button_frame,
            text="Next →",
            command=self._validate_api_and_continue,
            width=120
        )
        next_button.pack(side="right", padx=20, pady=10)
        
    def _create_preferences_step(self):
        """Create the preferences configuration step"""
        self._clear_content()
        self.current_step = 2
        
        # Progress indicator
        self._create_progress_indicator()
        
        # Step title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Application Preferences",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Customize your WindVoice experience",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Preferences frame
        prefs_frame = ctk.CTkFrame(self.main_frame)
        prefs_frame.pack(fill="x", padx=20, pady=10)
        
        # Theme selection
        ctk.CTkLabel(prefs_frame, text="Interface Theme", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        theme_frame = ctk.CTkFrame(prefs_frame)
        theme_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        dark_radio = ctk.CTkRadioButton(
            theme_frame,
            text="🌙 Dark (Recommended)",
            variable=self.theme_var,
            value="dark",
            command=self._on_theme_change
        )
        dark_radio.pack(side="left", padx=20, pady=10)
        
        light_radio = ctk.CTkRadioButton(
            theme_frame,
            text="☀️ Light",
            variable=self.theme_var,
            value="light",
            command=self._on_theme_change
        )
        light_radio.pack(side="left", padx=20, pady=10)
        
        # Notifications
        notifications_check = ctk.CTkCheckBox(
            prefs_frame,
            text="🔔 Show system tray notifications",
            variable=self.notifications_var,
            font=ctk.CTkFont(weight="bold")
        )
        notifications_check.pack(anchor="w", padx=20, pady=15)
        
        # Quick setup info
        info_frame = ctk.CTkFrame(self.main_frame)
        info_frame.pack(fill="x", padx=20, pady=15)
        
        info_title = ctk.CTkLabel(
            info_frame,
            text="🚀 Quick Setup Complete!",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        info_title.pack(pady=(15, 5))
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="After setup, you can:\\n"
                 "• Press Ctrl+Shift+Space anywhere to start recording\\n"
                 "• Right-click the system tray icon for advanced settings\\n"
                 "• Access audio device settings and more preferences",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        info_text.pack(pady=(0, 15))
        
        # Buttons
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        back_button = ctk.CTkButton(
            button_frame,
            text="← Back",
            command=self._create_api_step,
            width=100
        )
        back_button.pack(side="left", padx=20, pady=10)
        
        finish_button = ctk.CTkButton(
            button_frame,
            text="Complete Setup ✅",
            command=self._finish_setup,
            width=150,
            font=ctk.CTkFont(weight="bold")
        )
        finish_button.pack(side="right", padx=20, pady=10)
        
    def _create_progress_indicator(self):
        """Create progress indicator at top of window"""
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", pady=(10, 20))
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text=f"Step {self.current_step + 1} of {self.total_steps}",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        progress_label.pack(pady=10)
        
        # Progress bar
        progress_value = (self.current_step + 1) / self.total_steps
        progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        progress_bar.pack(pady=(0, 10))
        progress_bar.set(progress_value)
        
    def _clear_content(self):
        """Clear all content from main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
    def _validate_api_and_continue(self):
        """Validate API configuration before continuing"""
        api_key = self.api_key_var.get().strip()
        api_base = self.api_base_var.get().strip()
        key_alias = self.key_alias_var.get().strip()
        
        if not all([api_key, api_base, key_alias]):
            self.window.lift()
            self.window.focus_force()
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all required fields to continue.",
                parent=self.window
            )
            return
            
        # Basic validation
        if not api_key.startswith("sk-"):
            self.window.lift()
            self.window.focus_force()
            messagebox.showwarning(
                "Invalid API Key",
                "API key should start with 'sk-'. Please check your credentials.",
                parent=self.window
            )
            return

        if not api_base.startswith("http"):
            self.window.lift()
            self.window.focus_force()
            messagebox.showwarning(
                "Invalid API Base URL",
                "API base URL should start with 'http://' or 'https://'",
                parent=self.window
            )
            return
            
        self._create_preferences_step()
        
    def _on_theme_change(self):
        """Handle theme change"""
        theme = self.theme_var.get()
        ctk.set_appearance_mode(theme)
        
    def _finish_setup(self):
        """Complete the setup and save configuration"""
        try:
            # Create configuration
            config = WindVoiceConfig(
                litellm=LiteLLMConfig(
                    api_key=self.api_key_var.get().strip(),
                    api_base=self.api_base_var.get().strip(),
                    key_alias=self.key_alias_var.get().strip(),
                    model="whisper-1"
                ),
                app=AppConfig(),  # Use defaults
                ui=UIConfig(
                    theme=self.theme_var.get(),
                    window_position="center",
                    show_tray_notifications=self.notifications_var.get()
                )
            )

            # Save configuration
            self.config_manager.save_config(config)

            # Mark setup as completed
            self._mark_setup_completed()

            # Ensure messagebox appears on top of setup window
            self.window.lift()
            self.window.focus_force()
            messagebox.showinfo(
                "Setup Complete! 🎉",
                "WindVoice-Windows has been configured successfully!\\n\\n"
                "• Press Ctrl+Shift+Space to start voice recording\\n"
                "• Right-click the system tray icon for settings\\n\\n"
                "Welcome to fast voice-to-text transcription!",
                parent=self.window
            )

            # Mark as not visible and notify completion BEFORE closing window
            self.is_visible = False

            # Store completion callback to call after window is properly closed
            completion_callback = self.on_complete

            # Close the window first
            if self.window:
                # Schedule window destruction after a brief delay to ensure messagebox is fully closed
                self.window.after(100, self._complete_setup_and_close, completion_callback)
            else:
                # If no window, call completion directly
                if completion_callback:
                    completion_callback()

        except Exception as e:
            if self.window:
                self.window.lift()
                self.window.focus_force()
            messagebox.showerror("Setup Error", f"Failed to save configuration: {e}", parent=self.window if self.window else None)

    def _complete_setup_and_close(self, completion_callback):
        """Complete the setup process and close the window"""
        try:
            # Destroy the window
            if self.window:
                self.window.destroy()
                self.window = None

            # Call the completion callback after window is closed
            if completion_callback:
                completion_callback()

        except Exception as e:
            print(f"Error during setup completion: {e}")
            # Still try to call the completion callback
            if completion_callback:
                completion_callback()
            
    def _mark_setup_completed(self):
        """Mark that initial setup has been completed"""
        setup_marker = self.config_manager.config_dir / ".setup_completed"
        setup_marker.touch()
        
    def _on_close_attempt(self):
        """Handle attempt to close wizard before completion"""
        if self.window:
            self.window.lift()
            self.window.focus_force()
        result = messagebox.askyesno(
            "Exit Setup?",
            "WindVoice-Windows requires initial setup to function.\\n\\n"
            "Are you sure you want to exit without completing setup?\\n"
            "The application will not work until configured.",
            parent=self.window if self.window else None
        )
        
        if result:
            # Exit setup wizard if cancelled
            self.is_visible = False
            if self.window:
                self.window.destroy()
                self.window = None


def is_setup_needed(config_manager: ConfigManager) -> bool:
    """Check if initial setup is needed"""
    setup_marker = config_manager.config_dir / ".setup_completed"
    config_file = config_manager.config_file
    
    # If setup marker exists, no setup needed
    if setup_marker.exists():
        return False
        
    # If config file doesn't exist, setup is needed
    if not config_file.exists():
        return True
        
    # If config file exists, check if it has valid credentials
    try:
        config = config_manager.load_config()
        # Check if API credentials are configured
        if all([config.litellm.api_key, config.litellm.api_base, config.litellm.key_alias]):
            # Valid config exists but no setup marker - create it automatically
            print("Found valid configuration - marking setup as completed")
            _mark_setup_completed_automatically(config_manager)
            return False
        else:
            # Config exists but credentials are incomplete
            return True
    except Exception as e:
        print(f"Error loading config: {e}")
        return True
        
    return True


def _mark_setup_completed_automatically(config_manager: ConfigManager):
    """Mark setup as completed automatically when valid config is found"""
    try:
        setup_marker = config_manager.config_dir / ".setup_completed"
        setup_marker.touch()
        print(f"Setup completion marker created at: {setup_marker}")
    except Exception as e:
        print(f"Warning: Could not create setup marker: {e}")


def run_setup_if_needed(config_manager: ConfigManager, on_complete: Optional[Callable] = None) -> bool:
    """Run setup wizard if needed. Returns True if setup was run, False if it failed."""
    if not is_setup_needed(config_manager):
        return False
        
    print("First run detected - initializing setup wizard...")
    
    # Ensure config directory exists first
    config_manager.ensure_config_dir()
    
    # Try multiple approaches to ensure the setup wizard shows
    attempts = [
        ("CustomTkinter setup wizard", _try_customtkinter_setup),
        ("Basic Tkinter setup wizard", _try_basic_tkinter_setup),
        ("Console setup wizard", _try_console_setup)
    ]
    
    for attempt_name, attempt_func in attempts:
        try:
            print(f"Attempting {attempt_name}...")
            result = attempt_func(config_manager, on_complete)
            if result:
                print(f"✅ {attempt_name} succeeded")
                return True
            else:
                print(f"❌ {attempt_name} failed")
        except Exception as e:
            print(f"❌ {attempt_name} failed with error: {e}")
            continue
    
    print("❌ All setup wizard attempts failed - application will create template config")
    return False


def _try_customtkinter_setup(config_manager: ConfigManager, on_complete: Optional[Callable] = None) -> bool:
    """Try to create setup wizard with CustomTkinter using a simpler blocking approach"""
    try:
        # Create a simple blocking setup wizard
        return _create_simple_blocking_setup(config_manager, on_complete)
    except Exception as e:
        print(f"Simple setup failed: {e}")
        return False

def _create_simple_blocking_setup(config_manager: ConfigManager, on_complete: Optional[Callable] = None) -> bool:
    """Create a simple setup wizard that blocks until completed"""
    import customtkinter as ctk
    import tkinter as tk
    from tkinter import messagebox
    
    # Set CustomTkinter theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create the main window
    root = ctk.CTk()
    root.title("WindVoice-Windows Setup")
    root.geometry("600x500")
    root.resizable(False, False)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (300)
    y = (root.winfo_screenheight() // 2) - (250)
    root.geometry(f"600x500+{x}+{y}")
    
    # Make window stay on top
    root.attributes("-topmost", True)
    
    # Store widget references instead of using StringVar
    entry_widgets = {}
    
    # Result variable
    setup_completed = {"completed": False}
    
    def on_finish():
        """Handle finish button click"""
        # Get values directly from entry widgets
        api_key = entry_widgets["api_key"].get().strip()
        api_base = entry_widgets["api_base"].get().strip()
        key_alias = entry_widgets["key_alias"].get().strip()
        
        # Debug: Print the values to see what we got
        print(f"DEBUG - API Key: '{api_key}' (length: {len(api_key)})")
        print(f"DEBUG - API Base: '{api_base}' (length: {len(api_base)})")
        print(f"DEBUG - Key Alias: '{key_alias}' (length: {len(key_alias)})")
        
        # Validate inputs
        if not all([api_key, api_base, key_alias]):
            print("DEBUG - Validation failed: one or more fields are empty")
            root.lift()
            root.focus_force()
            messagebox.showwarning(
                "Missing Information",
                f"Please fill in all required fields.\nAPI Key: {'✓' if api_key else '✗'}\nAPI Base: {'✓' if api_base else '✗'}\nUser ID: {'✓' if key_alias else '✗'}",
                parent=root
            )
            return

        if not api_key.startswith("sk-"):
            root.lift()
            root.focus_force()
            messagebox.showwarning("Invalid API Key", "API key should start with 'sk-'.", parent=root)
            return

        if not api_base.startswith("http"):
            root.lift()
            root.focus_force()
            messagebox.showwarning("Invalid API Base URL", "API base URL should start with 'http://' or 'https://'", parent=root)
            return
        
        # Save configuration
        try:
            from ..core.config import WindVoiceConfig, LiteLLMConfig, AppConfig, UIConfig
            
            config = WindVoiceConfig(
                litellm=LiteLLMConfig(
                    api_key=api_key,
                    api_base=api_base,
                    key_alias=key_alias,
                    model="whisper-1"
                ),
                app=AppConfig(),
                ui=UIConfig()
            )
            
            config_manager.save_config(config)
            
            # Mark setup as completed
            setup_marker = config_manager.config_dir / ".setup_completed"
            setup_marker.touch()
            
            setup_completed["completed"] = True
            # Ensure messagebox appears on top
            root.lift()
            root.focus_force()
            messagebox.showinfo(
                "Setup Complete!",
                "WindVoice-Windows has been configured successfully!\\n\\nThe application will now start in the system tray.",
                parent=root
            )
            # Use destroy() instead of quit() to properly close the window
            root.destroy()
            
        except Exception as e:
            root.lift()
            root.focus_force()
            messagebox.showerror("Setup Error", f"Failed to save configuration: {e}", parent=root)

    def on_close():
        """Handle window close"""
        root.lift()
        root.focus_force()
        result = messagebox.askyesno(
            "Exit Setup?",
            "WindVoice-Windows requires setup to function. Exit without completing setup?",
            parent=root
        )
        if result:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    # Create UI
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = ctk.CTkLabel(
        main_frame,
        text="WindVoice-Windows Setup",
        font=ctk.CTkFont(size=24, weight="bold")
    )
    title_label.pack(pady=(20, 30))
    
    # Form
    form_frame = ctk.CTkFrame(main_frame)
    form_frame.pack(fill="x", padx=20, pady=10)
    
    # API Key
    ctk.CTkLabel(form_frame, text="API Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
    entry_widgets["api_key"] = ctk.CTkEntry(
        form_frame,
        placeholder_text="sk-your-api-key-here",
        show="*",
        width=400
    )
    entry_widgets["api_key"].pack(pady=(0, 10), padx=20)
    
    # API Base
    ctk.CTkLabel(form_frame, text="API Base URL:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
    entry_widgets["api_base"] = ctk.CTkEntry(
        form_frame,
        placeholder_text="https://your-litellm-proxy.company.com",
        width=400
    )
    entry_widgets["api_base"].pack(pady=(0, 10), padx=20)
    
    # Key Alias
    ctk.CTkLabel(form_frame, text="User ID:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
    entry_widgets["key_alias"] = ctk.CTkEntry(
        form_frame,
        placeholder_text="your-username",
        width=400
    )
    entry_widgets["key_alias"].pack(pady=(0, 20), padx=20)
    
    # Buttons
    button_frame = ctk.CTkFrame(main_frame)
    button_frame.pack(fill="x", padx=20, pady=20)
    
    finish_button = ctk.CTkButton(
        button_frame,
        text="Complete Setup",
        command=on_finish,
        width=200,
        height=40,
        font=ctk.CTkFont(weight="bold")
    )
    finish_button.pack(pady=20)
    
    print("Starting setup wizard mainloop...")
    root.mainloop()
    root.destroy()
    
    if setup_completed["completed"] and on_complete:
        on_complete()
    
    return setup_completed["completed"]


def _try_basic_tkinter_setup(config_manager: ConfigManager, on_complete: Optional[Callable] = None) -> bool:
    """Try to create setup wizard with basic Tkinter"""
    # For now, skip this step - we'll implement it later if needed
    return False


def _try_console_setup(config_manager: ConfigManager, on_complete: Optional[Callable] = None) -> bool:
    """Try console-based setup as last resort"""
    print("\n" + "="*60)
    print("WINDVOICE-WINDOWS CONSOLE SETUP")
    print("="*60)
    print("GUI setup failed. Let's configure WindVoice through the console.")
    print("Please provide your Thomson Reuters LiteLLM credentials:")
    
    try:
        api_key = input("API Key (starts with 'sk-'): ").strip()
        if not api_key.startswith("sk-"):
            print("Invalid API key format")
            return False
            
        api_base = input("API Base URL (https://...): ").strip()
        if not api_base.startswith("http"):
            print("Invalid API base URL format")
            return False
            
        key_alias = input("User ID/Key Alias: ").strip()
        if not key_alias:
            print("User ID cannot be empty")
            return False
        
        # Create and save configuration
        from ..core.config import WindVoiceConfig, LiteLLMConfig, AppConfig, UIConfig
        
        config = WindVoiceConfig(
            litellm=LiteLLMConfig(
                api_key=api_key,
                api_base=api_base,
                key_alias=key_alias,
                model="whisper-1"
            ),
            app=AppConfig(),
            ui=UIConfig()
        )
        
        config_manager.save_config(config)
        _mark_setup_completed_automatically(config_manager)
        
        print("✅ Configuration saved successfully!")
        print("WindVoice-Windows is now ready to use.")
        
        if on_complete:
            on_complete()
            
        return True
        
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        return False
    except Exception as e:
        print(f"Console setup failed: {e}")
        return False


def _provide_manual_setup_guidance(config_manager: ConfigManager):
    """Provide guidance for manual setup when GUI is not available"""
    config_file = config_manager.config_file
    
    try:
        # Ensure config directory exists
        config_manager.ensure_config_dir()
        
        # Create template config file if it doesn't exist
        if not config_file.exists():
            template_config = """# WindVoice-Windows Configuration File
# Replace the placeholder values below with your actual credentials

[litellm]
api_key = "sk-your-litellm-api-key-here"
api_base = "https://your-litellm-proxy-url-here"
key_alias = "your-username-or-id-here"
model = "whisper-1"

[app]
hotkey = "ctrl+shift+space"
audio_device = "default"
sample_rate = 44100

[ui]
theme = "dark"
window_position = "center"
show_tray_notifications = true
"""
            config_file.write_text(template_config, encoding='utf-8')
            print(f"Created configuration template at: {config_file}")
        
    except Exception as e:
        print(f"Error creating template config: {e}")
    
    print("\n" + "="*60)
    print("WINDVOICE-WINDOWS SETUP GUIDANCE")
    print("="*60)
    print("The setup wizard could not be displayed, but we've created a template configuration.")
    print(f"\nConfiguration file location: {config_file}")
    print("\nTo complete setup:")
    print("1. Edit the configuration file with your Thomson Reuters LiteLLM credentials")
    print("2. Replace the placeholder values with your actual API information")
    print("3. Save the file and restart WindVoice-Windows")
    print("4. Contact your IT administrator for LiteLLM credentials if needed")
    print("="*60)