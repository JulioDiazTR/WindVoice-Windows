"""
WindVoice Popup Window

Smart transcription popup with keyboard shortcuts and auto-positioning.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
from typing import Optional, Callable
import pyperclip

from ..services.injection import TextInjectionService


class TranscriptionPopup:
    def __init__(self, text: str, on_close: Optional[Callable] = None, parent_window=None):
        self.text = text
        self.on_close = on_close
        self.parent_window = parent_window
        self.text_injection_service = TextInjectionService()
        
        # Window setup
        self.window: Optional[ctk.CTkToplevel] = None
        self.is_visible = False
        
    def show(self):
        """Show the popup - user controls when to close"""
        if self.window and self.is_visible:
            self.window.lift()
            self.window.focus_force()
            return
            
        self._create_window()
        self._position_window()
        self.is_visible = True
        
    def hide(self):
        """Hide the popup"""
        try:
            if self.window:
                try:
                    self.window.destroy()
                except Exception as destroy_error:
                    print(f"Warning: Error destroying popup window: {destroy_error}")
                finally:
                    self.window = None
                    
            self.is_visible = False
            
            if self.on_close:
                try:
                    self.on_close()
                except Exception as callback_error:
                    print(f"Warning: Error in popup close callback: {callback_error}")
        except Exception as e:
            print(f"Error in popup hide(): {e}")
            # Ensure visibility flag is reset even if there are errors
            self.is_visible = False
    
    def _create_window(self):
        """Create the popup window"""
        try:
            # Use parent window if provided, otherwise try to find the root
            if self.parent_window:
                self.window = ctk.CTkToplevel(self.parent_window)
            else:
                # Try to get the main Tkinter root window if available
                try:
                    import tkinter as tk
                    root = tk._default_root
                    if root is not None:
                        self.window = ctk.CTkToplevel(root)
                    else:
                        self.window = ctk.CTkToplevel()
                except:
                    self.window = ctk.CTkToplevel()
                
            self.window.title("WindVoice - Transcription")
            self.window.geometry("550x350")
            self.window.resizable(True, True)
            self.window.minsize(400, 250)
        except Exception as e:
            print(f"Error creating popup window: {e}")
            raise
        
        # Make window stay on top
        self.window.attributes("-topmost", True)
        
        # Window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        
        # Bind keyboard shortcuts
        self.window.bind("<Return>", lambda e: self.hide())
        self.window.bind("<Control-c>", self._on_copy)
        self.window.bind("<Escape>", lambda e: self.hide())
        
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
        
        # Insert text and select all
        self.text_widget.insert("1.0", self.text)
        # Use CTkTextbox compatible selection method
        try:
            # Try the tkinter standard method first
            self.text_widget.tag_add("sel", "1.0", "end")
            self.text_widget.mark_set("insert", "1.0")
        except:
            # If that fails, just focus without selection
            pass
        self.text_widget.focus()
        
        # Button frame with more height
        button_frame = ctk.CTkFrame(main_frame, height=80)
        button_frame.pack(fill="x", pady=(10, 10))
        button_frame.pack_propagate(False)  # Maintain fixed height
        
        # Action buttons - simplified interface with proper sizing
        copy_button = ctk.CTkButton(
            button_frame,
            text="📋 Copy (Ctrl+C)",
            command=self._copy_text,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        copy_button.pack(side="left", padx=(20, 10), pady=20)
        
        close_button = ctk.CTkButton(
            button_frame,
            text="✅ Close (Enter/Esc)",
            command=self.hide,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        close_button.pack(side="right", padx=(10, 20), pady=20)
        
        # Shortcuts info
        info_label = ctk.CTkLabel(
            main_frame,
            text="💡 Shortcuts: Ctrl+C=Copy to Clipboard | Enter/Esc=Close",
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
            
            
    def _on_copy(self, event):
        """Handle Ctrl+C keyboard shortcut"""
        self._copy_text()
        return "break"  # Prevent default text widget copy behavior
        
        


class SmartTranscriptionPopup(TranscriptionPopup):
    """Enhanced popup with smart positioning and context awareness"""
    
    def __init__(self, text: str, context: Optional[str] = None, on_close: Optional[Callable] = None, parent_window=None):
        super().__init__(text, on_close, parent_window)
        self.context = context
        
    def show_with_focus(self):
        """Show popup with smart focus handling"""
        self.show()
        
        # Simple focus handling without threading
        if self.window and self.context:
            try:
                # Schedule focus adjustment in the main UI thread
                self.window.after(500, self._restore_focus_safe)
            except Exception as e:
                print(f"Warning: Could not schedule focus restoration: {e}")
                
    def _restore_focus_safe(self):
        """Safely restore focus in the main UI thread"""
        try:
            if self.window and self.is_visible:
                self.window.attributes("-topmost", False)
                self.window.attributes("-topmost", True)
        except Exception as e:
            print(f"Warning: Could not restore focus context: {e}")


# Factory functions for creating popups
def show_transcription_popup(text: str, parent_window=None) -> TranscriptionPopup:
    """Create and show a basic transcription popup"""
    popup = TranscriptionPopup(text, parent_window=parent_window)
    popup.show()
    return popup


def show_smart_popup(text: str, context: Optional[str] = None, timeout: int = 15, parent_window=None) -> SmartTranscriptionPopup:
    """Create and show a smart transcription popup with context awareness"""
    try:
        popup = SmartTranscriptionPopup(text, context, parent_window=parent_window)
        popup.show_with_focus()
        return popup
    except Exception as e:
        print(f"Error creating smart popup: {e}")
        # Fallback to basic popup
        try:
            popup = TranscriptionPopup(text, parent_window=parent_window)
            popup.show()
            return popup
        except Exception as fallback_e:
            print(f"Error creating fallback popup: {fallback_e}")
            # Re-raise the original error
            raise e