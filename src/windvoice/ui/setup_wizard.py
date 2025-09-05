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
        
    def hide(self):
        """Hide the setup wizard"""
        if self.window:
            self.window.withdraw()
            self.is_visible = False
    
    def _create_window(self):
        """Create the main setup window"""
        # Initialize variables
        self.api_key_var = ctk.StringVar()
        self.api_base_var = ctk.StringVar()
        self.key_alias_var = ctk.StringVar()
        self.theme_var = ctk.StringVar(value="dark")
        self.notifications_var = ctk.BooleanVar(value=True)
        
        self.window = ctk.CTkToplevel()
        self.window.title("WindVoice-Windows Setup")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        
        # Make window modal
        self.window.transient()
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Prevent closing without completing setup
        self.window.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main container
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._create_welcome_step()
        
    def _create_welcome_step(self):
        """Create the welcome step"""
        self._clear_content()
        self.current_step = 0
        
        # Progress indicator
        self._create_progress_indicator()
        
        # Welcome content
        welcome_label = ctk.CTkLabel(
            self.main_frame,
            text="Welcome to WindVoice-Windows! 🎙️",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        welcome_label.pack(pady=(40, 20))
        
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
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all required fields to continue."
            )
            return
            
        # Basic validation
        if not api_key.startswith("sk-"):
            messagebox.showwarning(
                "Invalid API Key",
                "API key should start with 'sk-'. Please check your credentials."
            )
            return
            
        if not api_base.startswith("http"):
            messagebox.showwarning(
                "Invalid API Base URL", 
                "API base URL should start with 'http://' or 'https://'"
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
            
            messagebox.showinfo(
                "Setup Complete! 🎉",
                "WindVoice-Windows has been configured successfully!\\n\\n"
                "• Press Ctrl+Shift+Space to start voice recording\\n"
                "• Right-click the system tray icon for settings\\n\\n"
                "Welcome to fast voice-to-text transcription!"
            )
            
            # Close wizard and notify completion
            self.window.destroy()
            self.is_visible = False
            
            if self.on_complete:
                self.on_complete()
                
        except Exception as e:
            messagebox.showerror("Setup Error", f"Failed to save configuration: {e}")
            
    def _mark_setup_completed(self):
        """Mark that initial setup has been completed"""
        setup_marker = self.config_manager.config_dir / ".setup_completed"
        setup_marker.touch()
        
    def _on_close_attempt(self):
        """Handle attempt to close wizard before completion"""
        result = messagebox.askyesno(
            "Exit Setup?",
            "WindVoice-Windows requires initial setup to function.\\n\\n"
            "Are you sure you want to exit without completing setup?\\n"
            "The application will not work until configured."
        )
        
        if result:
            # Exit the entire application if setup is cancelled
            self.window.quit()


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
    """Run setup wizard if needed. Returns True if setup was run."""
    if is_setup_needed(config_manager):
        try:
            # Try to run the GUI setup wizard
            wizard = SetupWizard(config_manager, on_complete)
            wizard.show()
            return True
        except Exception as e:
            print(f"Warning: Could not launch setup wizard GUI: {e}")
            print("This might be due to running in a headless environment or missing GUI libraries.")
            
            # Try to provide helpful guidance for manual setup
            _provide_manual_setup_guidance(config_manager)
            return False
    return False


def _provide_manual_setup_guidance(config_manager: ConfigManager):
    """Provide guidance for manual setup when GUI is not available"""
    config_file = config_manager.config_file
    
    print("\n" + "="*60)
    print("WINDVOICE-WINDOWS MANUAL SETUP REQUIRED")
    print("="*60)
    print("The setup wizard could not be displayed. Please create the configuration manually:")
    print(f"\n1. Create/edit the config file at: {config_file}")
    print("\n2. Add the following content (replace with your actual credentials):")
    print("""
[litellm]
api_key = "sk-your-litellm-api-key"
api_base = "https://your-litellm-proxy-url"
key_alias = "your-username-or-id"
model = "whisper-1"

[app]
hotkey = "ctrl+shift+space"
sample_rate = 44100

[ui]
theme = "dark"
window_position = "center"
show_tray_notifications = true
""")
    print("3. Save the file and restart WindVoice-Windows")
    print("\n4. Contact your IT administrator for LiteLLM credentials if needed")
    print("="*60)
    
    # Create example config if it doesn't exist
    try:
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                f.write("""# WindVoice-Windows Configuration
# Please fill in your LiteLLM credentials below

[litellm]
api_key = ""  # Your LiteLLM API key (starts with sk-)
api_base = ""  # Your LiteLLM proxy URL (https://your-proxy.com)
key_alias = ""  # Your username or employee ID
model = "whisper-1"

[app]
hotkey = "ctrl+shift+space"
sample_rate = 44100

[ui]
theme = "dark"
window_position = "center"
show_tray_notifications = true
""")
            print(f"Template configuration file created at: {config_file}")
    except Exception as e:
        print(f"Could not create template config: {e}")