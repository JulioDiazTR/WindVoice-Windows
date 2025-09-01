"""
Simple, highly visible status feedback using multiple approaches
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
from typing import Optional
from enum import Enum

class StatusType(Enum):
    RECORDING = "recording"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"

class SimpleVisibleStatus:
    """
    Ultra-simple status feedback that guarantees visibility using multiple methods
    """
    
    def __init__(self):
        self.current_window: Optional[tk.Toplevel] = None
        self.auto_hide_job: Optional[str] = None
        
    def show_status(self, status_type: StatusType, duration: float = 3.0):
        """Show status with guaranteed visibility"""
        
        # Hide any existing window
        self.hide()
        
        # Method 1: Simple Tkinter window with high visibility
        try:
            self._show_simple_window(status_type, duration)
        except Exception as e:
            print(f"Simple window failed: {e}")
            # Method 2: Fallback to console + system notification
            self._show_console_status(status_type)
            
    def _show_simple_window(self, status_type: StatusType, duration: float):
        """Create a simple, highly visible window"""
        
        # Create root if needed
        try:
            root = tk._default_root
            if root is None:
                root = tk.Tk()
                root.withdraw()
        except:
            root = tk.Tk()
            root.withdraw()
            
        # Create visible toplevel window
        self.current_window = tk.Toplevel(root)
        
        # Configure for maximum visibility
        self.current_window.title("WindVoice Status")
        self.current_window.geometry("200x100")
        self.current_window.attributes("-topmost", True)
        self.current_window.attributes("-toolwindow", True)
        self.current_window.resizable(False, False)
        
        # Position in center-right of screen
        screen_width = self.current_window.winfo_screenwidth()
        screen_height = self.current_window.winfo_screenheight()
        x = screen_width - 250  # Right side with margin
        y = screen_height // 2 - 50  # Center vertically
        self.current_window.geometry(f"200x100+{x}+{y}")
        
        # Style based on status
        if status_type == StatusType.RECORDING:
            bg_color = "#ff4444"
            text_color = "white"
            message = "🎤 GRABANDO"
        elif status_type == StatusType.PROCESSING:
            bg_color = "#4444ff"
            text_color = "white"
            message = "⚡ PROCESANDO"
        elif status_type == StatusType.SUCCESS:
            bg_color = "#44ff44"
            text_color = "black"
            message = "✅ ÉXITO"
        else:  # ERROR
            bg_color = "#ff8844"
            text_color = "white"
            message = "❌ ERROR"
            
        self.current_window.configure(bg=bg_color)
        
        # Large, visible text
        label = tk.Label(
            self.current_window,
            text=message,
            font=('Arial', 14, 'bold'),
            bg=bg_color,
            fg=text_color
        )
        label.pack(expand=True, fill='both')
        
        # Force visibility
        self.current_window.deiconify()
        self.current_window.lift()
        self.current_window.focus_force()
        self.current_window.update()
        
        # Auto-hide after duration using Tkinter's after method (thread-safe)
        if duration > 0:
            def auto_hide():
                try:
                    if self.current_window:
                        self.current_window.destroy()
                        self.current_window = None
                        self.auto_hide_job = None
                except:
                    pass
                    
            # Convert duration to milliseconds and use Tkinter's after method
            self.auto_hide_job = self.current_window.after(int(duration * 1000), auto_hide)
        
        
    def _show_console_status(self, status_type: StatusType):
        """Fallback: show status in console with system notification"""
        
        messages = {
            StatusType.RECORDING: "🎤 GRABANDO - Presiona el hotkey para detener",
            StatusType.PROCESSING: "⚡ PROCESANDO - Transcribiendo audio...",
            StatusType.SUCCESS: "✅ ÉXITO - Texto insertado correctamente",
            StatusType.ERROR: "❌ ERROR - Hubo un problema con la transcripción"
        }
        
        message = messages.get(status_type, "Status update")
        print(f"\n{'='*50}")
        print(f"WINDVOICE STATUS: {message}")
        print(f"{'='*50}\n")
        
        # Try Windows toast notification
        try:
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(
                "WindVoice",
                message,
                duration=3,
                threaded=True
            )
        except ImportError:
            # Try plyer as alternative
            try:
                from plyer import notification
                notification.notify(
                    title="WindVoice",
                    message=message,
                    timeout=3
                )
            except ImportError:
                print("No notification system available - status shown in console only")
                
    def hide(self):
        """Hide current status window"""
        # Cancel any pending auto-hide
        if self.auto_hide_job and self.current_window:
            try:
                self.current_window.after_cancel(self.auto_hide_job)
                self.auto_hide_job = None
            except:
                pass
                
        # Destroy window
        if self.current_window:
            try:
                self.current_window.destroy()
            except:
                pass
            self.current_window = None

class SimpleVisibleStatusManager:
    """Manager for simple visible status"""
    
    def __init__(self):
        self.status = SimpleVisibleStatus()
        
    def show_recording(self):
        """Show recording status"""
        self.status.show_status(StatusType.RECORDING, 0)  # Show indefinitely
        
    def show_processing(self):
        """Show processing status"""  
        self.status.show_status(StatusType.PROCESSING, 0)  # Show indefinitely
        
    def show_success(self):
        """Show success status"""
        self.status.show_status(StatusType.SUCCESS, 2.0)  # Auto-hide after 2 seconds
        
    def show_error(self):
        """Show error status"""
        self.status.show_status(StatusType.ERROR, 3.0)  # Auto-hide after 3 seconds
        
    def update_audio_level(self, level: float):
        """Update audio level (not implemented for simple version)"""
        pass
        
    def hide(self):
        """Hide status"""
        self.status.hide()
        
    def is_visible(self) -> bool:
        """Check if status is visible"""
        return self.status.current_window is not None


# Test function
def test_simple_visible():
    """Test the simple visible status"""
    print("=== TEST SIMPLE VISIBLE STATUS ===")
    
    manager = SimpleVisibleStatusManager()
    
    def test_sequence():
        print("1. Testing RECORDING...")
        manager.show_recording()
        time.sleep(3)
        
        print("2. Testing PROCESSING...")
        manager.show_processing()
        time.sleep(3)
        
        print("3. Testing SUCCESS...")
        manager.show_success()
        time.sleep(3)
        
        print("4. Testing ERROR...")
        manager.show_error()
        time.sleep(4)
        
        print("Test completed!")
        
    test_sequence()

if __name__ == "__main__":
    test_simple_visible()