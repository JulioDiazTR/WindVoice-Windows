"""
WindVoice Popup Window

Smart transcription popup with keyboard shortcuts and auto-positioning.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
from typing import Optional, Callable
import pyperclip

from ..services.injection import TextInjectionService


class TranscriptionPopup:
    def __init__(self, text: str, on_close: Optional[Callable] = None):
        self.text = text
        self.on_close = on_close
        self.text_injection_service = TextInjectionService()
        
        # Window setup
        self.window: Optional[ctk.CTkToplevel] = None
        self.is_visible = False
        self.auto_dismiss_timer: Optional[threading.Timer] = None
        
    def show(self, timeout_seconds: int = 10):
        """Show the popup with optional auto-dismiss timeout"""
        if self.window and self.is_visible:
            self.window.lift()
            self.window.focus_force()
            return
            
        self._create_window()
        self._position_window()
        self.is_visible = True
        
        # Set up auto-dismiss timer
        if timeout_seconds > 0:
            self.auto_dismiss_timer = threading.Timer(timeout_seconds, self._auto_dismiss)
            self.auto_dismiss_timer.start()
        
    def hide(self):
        """Hide the popup"""
        if self.auto_dismiss_timer:
            self.auto_dismiss_timer.cancel()
            
        if self.window:
            self.window.destroy()
            self.window = None
            
        self.is_visible = False
        
        if self.on_close:
            self.on_close()
    
    def _create_window(self):
        """Create the popup window"""
        self.window = ctk.CTkToplevel()
        self.window.title("WindVoice - Transcription")
        self.window.geometry("500x300")
        self.window.resizable(True, True)
        
        # Make window stay on top
        self.window.attributes("-topmost", True)
        
        # Window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        
        # Bind keyboard shortcuts
        self.window.bind("<Return>", self._on_paste_and_close)
        self.window.bind("<Control-c>", self._on_copy)
        self.window.bind("<Escape>", lambda e: self.hide())
        self.window.bind("<Control-Return>", self._on_inject_text)
        
        # Create widgets
        self._create_widgets()
        
        # Focus the window for keyboard input
        self.window.focus_force()
        
    def _create_widgets(self):
        """Create popup widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎤 Voice Transcription",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Text display (scrollable)
        self.text_widget = ctk.CTkTextbox(
            main_frame,
            height=150,
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        self.text_widget.pack(fill="both", expand=True, pady=(0, 15))
        
        # Insert and select all text
        self.text_widget.insert("1.0", self.text)
        self.text_widget.select_range("1.0", "end")
        self.text_widget.focus()
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Action buttons
        copy_button = ctk.CTkButton(
            button_frame,
            text="📋 Copy (Ctrl+C)",
            command=self._copy_text,
            width=120
        )
        copy_button.pack(side="left", padx=(10, 5), pady=10)
        
        paste_button = ctk.CTkButton(
            button_frame,
            text="📝 Paste & Close (Enter)",
            command=self._paste_and_close,
            width=150
        )
        paste_button.pack(side="left", padx=5, pady=10)
        
        inject_button = ctk.CTkButton(
            button_frame,
            text="💉 Inject Text (Ctrl+Enter)",
            command=self._inject_text,
            width=150
        )
        inject_button.pack(side="left", padx=5, pady=10)
        
        close_button = ctk.CTkButton(
            button_frame,
            text="❌ Close (Esc)",
            command=self.hide,
            width=100
        )
        close_button.pack(side="right", padx=(5, 10), pady=10)
        
        # Shortcuts info
        info_label = ctk.CTkLabel(
            main_frame,
            text="💡 Shortcuts: Enter=Paste & Close | Ctrl+C=Copy | Ctrl+Enter=Inject | Esc=Close",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray40")
        )
        info_label.pack(pady=(5, 10))
        
    def _position_window(self):
        """Position window near cursor or center of screen"""
        try:
            # Update window to get actual dimensions
            self.window.update_idletasks()
            
            # Get screen dimensions
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # Get window dimensions
            window_width = self.window.winfo_reqwidth()
            window_height = self.window.winfo_reqheight()
            
            # Try to get cursor position (fallback to center if not available)
            try:
                import win32gui
                cursor_x, cursor_y = win32gui.GetCursorPos()
                
                # Position near cursor with offset
                x = cursor_x + 20
                y = cursor_y + 20
                
                # Ensure window stays on screen
                if x + window_width > screen_width:
                    x = screen_width - window_width - 20
                if y + window_height > screen_height:
                    y = screen_height - window_height - 20
                    
            except ImportError:
                # Fallback to center of screen
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                
            self.window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            # If positioning fails, just center the window
            print(f"Warning: Could not position popup window: {e}")
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() - self.window.winfo_reqwidth()) // 2
            y = (self.window.winfo_screenheight() - self.window.winfo_reqheight()) // 2
            self.window.geometry(f"+{x}+{y}")
            
    def _copy_text(self):
        """Copy transcribed text to clipboard"""
        try:
            # Get current text from widget (in case user edited it)
            current_text = self.text_widget.get("1.0", "end-1c")
            pyperclip.copy(current_text)
            
            # Brief visual feedback
            original_text = self.window.title()
            self.window.title("✅ Copied to clipboard!")
            self.window.after(1500, lambda: self.window.title(original_text))
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy text: {e}")
            
    def _paste_and_close(self):
        """Copy text to clipboard and close popup"""
        try:
            current_text = self.text_widget.get("1.0", "end-1c")
            pyperclip.copy(current_text)
            
            # Use system paste shortcut to paste into active application
            import pyautogui
            time.sleep(0.1)  # Brief delay
            self.hide()  # Hide popup first
            time.sleep(0.1)  # Brief delay for window focus to return
            pyautogui.hotkey('ctrl', 'v')
            
        except Exception as e:
            messagebox.showerror("Paste Error", f"Failed to paste text: {e}")
            
    def _inject_text(self):
        """Directly inject text into active application"""
        try:
            current_text = self.text_widget.get("1.0", "end-1c")
            
            # Hide popup first to restore focus to target application
            self.hide()
            time.sleep(0.1)  # Brief delay for focus change
            
            # Inject text directly
            success = self.text_injection_service.inject_text(current_text)
            
            if not success:
                # If injection fails, show error and reopen popup
                messagebox.showerror(
                    "Injection Failed", 
                    "Failed to inject text. Text has been copied to clipboard instead."
                )
                pyperclip.copy(current_text)
                
        except Exception as e:
            messagebox.showerror("Injection Error", f"Failed to inject text: {e}")
            # Fallback to clipboard
            pyperclip.copy(self.text_widget.get("1.0", "end-1c"))
            
    def _on_copy(self, event):
        """Handle Ctrl+C keyboard shortcut"""
        self._copy_text()
        return "break"  # Prevent default text widget copy behavior
        
    def _on_paste_and_close(self, event):
        """Handle Enter keyboard shortcut"""
        self._paste_and_close()
        return "break"
        
    def _on_inject_text(self, event):
        """Handle Ctrl+Enter keyboard shortcut"""
        self._inject_text()
        return "break"
        
    def _auto_dismiss(self):
        """Auto-dismiss the popup after timeout"""
        if self.is_visible:
            print("Auto-dismissing transcription popup after timeout")
            self.hide()


class SmartTranscriptionPopup(TranscriptionPopup):
    """Enhanced popup with smart positioning and context awareness"""
    
    def __init__(self, text: str, context: Optional[str] = None, on_close: Optional[Callable] = None):
        super().__init__(text, on_close)
        self.context = context
        
    def show_with_focus(self, timeout_seconds: int = 15):
        """Show popup with smart focus handling"""
        self.show(timeout_seconds)
        
        # Try to restore focus to the original application after a delay
        if self.context:
            threading.Timer(0.5, self._restore_focus).start()
            
    def _restore_focus(self):
        """Restore focus to the previously active window"""
        try:
            # This could be enhanced with window management APIs
            # For now, just ensure our popup stays accessible
            if self.window and self.is_visible:
                self.window.attributes("-topmost", False)
                self.window.attributes("-topmost", True)
                
        except Exception as e:
            print(f"Warning: Could not restore focus context: {e}")


# Factory functions for creating popups
def show_transcription_popup(text: str, timeout: int = 10) -> TranscriptionPopup:
    """Create and show a basic transcription popup"""
    popup = TranscriptionPopup(text)
    popup.show(timeout)
    return popup


def show_smart_popup(text: str, context: Optional[str] = None, timeout: int = 15) -> SmartTranscriptionPopup:
    """Create and show a smart transcription popup with context awareness"""
    popup = SmartTranscriptionPopup(text, context)
    popup.show_with_focus(timeout)
    return popup