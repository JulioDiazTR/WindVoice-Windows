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
        
        # Dragging state
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Position persistence
        self.custom_position = None  # (x, y) if user has moved the window
        self.user_moved_window = False
        
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
        """Create a modern, transparent window near cursor"""
        
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
        
        # Configure for modern transparent appearance WITHOUT stealing focus
        self.current_window.title("WindVoice Status")
        self.current_window.geometry("160x80")  # More compact
        self.current_window.attributes("-topmost", True)
        self.current_window.attributes("-toolwindow", True)
        self.current_window.attributes("-alpha", 0.5)  # Even more transparent
        self.current_window.resizable(False, False)
        self.current_window.overrideredirect(True)  # Remove window decorations
        
        # CRITICAL: Make window non-focusable to preserve text field focus
        try:
            # Windows-specific: Make window non-focusable using Win32 API
            import ctypes
            from ctypes import wintypes
            
            # Get window handle
            hwnd = self.current_window.winfo_id()
            
            # Set WS_EX_NOACTIVATE extended style to prevent focus stealing
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            
            # Get current extended style
            current_style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            
            # Add WS_EX_NOACTIVATE flag
            new_style = current_style | WS_EX_NOACTIVATE
            
            # Apply new style
            ctypes.windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, new_style)
            
            print("✅ Status dialog configured as non-focusable")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not make status window non-focusable: {e}")
            # Continue anyway - the dialog will work but may steal focus
        
        # Position based on user preference or smart cursor placement
        window_width, window_height = 160, 80
        
        if self.user_moved_window and self.custom_position:
            # Use the custom position where user moved the window
            x, y = self.custom_position
            # Ensure the custom position is still valid (in case screen resolution changed)
            try:
                screen_width = self.current_window.winfo_screenwidth()
                screen_height = self.current_window.winfo_screenheight()
                x = max(0, min(x, screen_width - window_width))
                y = max(0, min(y, screen_height - window_height))
            except:
                pass
        else:
            # Smart positioning near cursor (first time or if user hasn't moved)
            cursor_x, cursor_y = self._get_cursor_position()
            monitor_info = self._get_active_monitor(cursor_x, cursor_y)
            
            margin = 30
            
            # Try positioning to bottom-right of cursor
            x = cursor_x + margin
            y = cursor_y + margin
            
            # Keep window within monitor bounds
            if x + window_width > monitor_info['right']:
                x = cursor_x - window_width - margin
            if y + window_height > monitor_info['bottom']:
                y = cursor_y - window_height - margin
                
            # Final bounds check
            x = max(monitor_info['left'], min(x, monitor_info['right'] - window_width))
            y = max(monitor_info['top'], min(y, monitor_info['bottom'] - window_height))
        
        self.current_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Modern glassmorphism style based on status
        if status_type == StatusType.RECORDING:
            bg_color = "#1a0000"  # Dark red base
            accent_color = "#ff4444"
            text_color = "white"
            message = "🎤 RECORDING"
            glow_color = "#ff6666"
        elif status_type == StatusType.PROCESSING:
            bg_color = "#00001a"  # Dark blue base  
            accent_color = "#4444ff"
            text_color = "white"
            message = "⚡ PROCESSING"
            glow_color = "#6666ff"
        elif status_type == StatusType.SUCCESS:
            bg_color = "#001a00"  # Dark green base
            accent_color = "#44ff44"
            text_color = "white"
            message = "✅ SUCCESS"
            glow_color = "#66ff66"
        else:  # ERROR
            bg_color = "#1a0a00"  # Dark orange base
            accent_color = "#ff8844"
            text_color = "white"
            message = "❌ ERROR"
            glow_color = "#ffaa66"
            
        self.current_window.configure(bg=bg_color)
        
        # Add Windows blur effect if available
        try:
            import ctypes
            hwnd = self.current_window.winfo_id()
            ctypes.windll.dwmapi.DwmEnableBlurBehindWindow(hwnd, ctypes.byref(ctypes.c_int(1)))
        except:
            pass
        
        # Create main container frame with rounded appearance
        main_frame = tk.Frame(
            self.current_window,
            bg=bg_color,
            relief='flat',
            bd=0
        )
        main_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Add subtle border effect with canvas
        canvas = tk.Canvas(
            main_frame,
            bg=bg_color,
            highlightthickness=1,
            highlightbackground=glow_color,
            relief='flat'
        )
        canvas.pack(fill='both', expand=True)
        
        # Add dragging functionality
        canvas.bind("<Button-1>", self._on_drag_start)
        canvas.bind("<B1-Motion>", self._on_drag_motion)
        canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        main_frame.bind("<Button-1>", self._on_drag_start)
        main_frame.bind("<B1-Motion>", self._on_drag_motion)
        main_frame.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Add hover effects for better interactivity
        canvas.bind("<Enter>", self._on_hover_enter)
        canvas.bind("<Leave>", self._on_hover_leave)
        
        # Modern text with shadow effect
        canvas.create_text(
            81, 41,  # Shadow position (slightly offset)
            text=message,
            font=('Segoe UI', 11, 'bold'),
            fill="#000000",
            anchor='center'
        )
        
        # Main text with glow effect
        canvas.create_text(
            80, 40,  # Main text position
            text=message,
            font=('Segoe UI', 11, 'bold'),
            fill=text_color,
            anchor='center'
        )
        
        # Force visibility WITHOUT stealing focus from active applications
        self.current_window.deiconify()
        self.current_window.lift()
        # REMOVED: self.current_window.focus_force()  # This steals focus from text fields!
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
    
    def _get_cursor_position(self):
        """Get current cursor position"""
        try:
            import win32gui
            return win32gui.GetCursorPos()
        except ImportError:
            # Fallback using tkinter if win32gui not available
            try:
                if self.current_window:
                    self.current_window.update_idletasks()
                    return self.current_window.winfo_pointerx(), self.current_window.winfo_pointery()
                else:
                    # Create temporary window to get pointer position
                    temp_root = tk.Tk()
                    temp_root.withdraw()
                    temp_root.update_idletasks()
                    x, y = temp_root.winfo_pointerx(), temp_root.winfo_pointery()
                    temp_root.destroy()
                    return x, y
            except:
                return 200, 200  # Default fallback position
    
    def _get_active_monitor(self, cursor_x, cursor_y):
        """Get information about the monitor containing the cursor"""
        try:
            import win32api
            
            # Get all monitors
            monitors = win32api.EnumDisplayMonitors()
            
            # Find monitor containing cursor
            for monitor_handle, device_context, monitor_rect in monitors:
                left, top, right, bottom = monitor_rect
                if left <= cursor_x < right and top <= cursor_y < bottom:
                    return {
                        'left': left,
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'width': right - left,
                        'height': bottom - top
                    }
            
            # Fallback to primary monitor if cursor monitor not found
            return self._get_primary_monitor()
            
        except ImportError:
            return self._get_primary_monitor()
    
    def _get_primary_monitor(self):
        """Get primary monitor information as fallback"""
        try:
            if self.current_window:
                self.current_window.update_idletasks()
                width = self.current_window.winfo_screenwidth()
                height = self.current_window.winfo_screenheight()
            else:
                # Create temporary window to get screen dimensions
                temp_root = tk.Tk()
                temp_root.withdraw()
                temp_root.update_idletasks()
                width = temp_root.winfo_screenwidth()
                height = temp_root.winfo_screenheight()
                temp_root.destroy()
                
            return {
                'left': 0,
                'top': 0,
                'right': width,
                'bottom': height,
                'width': width,
                'height': height
            }
        except:
            return {
                'left': 0, 'top': 0, 'right': 1920, 'bottom': 1080,
                'width': 1920, 'height': 1080
            }
    
    def _on_drag_start(self, event):
        """Start dragging the window WITHOUT stealing focus"""
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # Change cursor to indicate dragging
        if self.current_window:
            self.current_window.configure(cursor="fleur")
            # Slightly increase opacity when dragging
            self.current_window.attributes("-alpha", min(0.85, self.current_window.attributes("-alpha") + 0.2))
            
            # IMPORTANT: Don't focus the window during drag operations
            # This preserves focus in the original text field
    
    def _on_drag_motion(self, event):
        """Handle window dragging with smooth movement"""
        if self.current_window and self.dragging:
            # Calculate new position
            new_x = self.current_window.winfo_x() + (event.x - self.drag_start_x)
            new_y = self.current_window.winfo_y() + (event.y - self.drag_start_y)
            
            # Keep window within screen bounds
            try:
                screen_width = self.current_window.winfo_screenwidth()
                screen_height = self.current_window.winfo_screenheight()
                window_width = self.current_window.winfo_width()
                window_height = self.current_window.winfo_height()
                
                # Constrain to screen bounds
                new_x = max(0, min(new_x, screen_width - window_width))
                new_y = max(0, min(new_y, screen_height - window_height))
                
                # Apply new position
                self.current_window.geometry(f"+{new_x}+{new_y}")
            except:
                # If screen bounds check fails, still allow basic movement
                self.current_window.geometry(f"+{new_x}+{new_y}")
    
    def _on_drag_end(self, event):
        """End dragging with smooth transition"""
        self.dragging = False
        
        # Save the new position for future state changes
        if self.current_window:
            try:
                # Get current window position and save it
                self.current_window.update_idletasks()
                x = self.current_window.winfo_x()
                y = self.current_window.winfo_y()
                self.custom_position = (x, y)
                self.user_moved_window = True
            except:
                pass
            
            # Restore cursor and transparency
            self.current_window.configure(cursor="")
            # Restore original transparency
            self.current_window.attributes("-alpha", 0.5)
    
    def _on_hover_enter(self, event):
        """Handle mouse hover enter - increase visibility slightly"""
        if self.current_window and not self.dragging:
            # Slightly increase opacity on hover for better interaction
            self.current_window.attributes("-alpha", min(0.8, self.current_window.attributes("-alpha") + 0.15))
    
    def _on_hover_leave(self, event):
        """Handle mouse hover leave - restore transparency"""
        if self.current_window and not self.dragging:
            # Restore original transparency
            self.current_window.attributes("-alpha", 0.5)
        
        
    def _show_console_status(self, status_type: StatusType):
        """Fallback: show status in console with system notification"""
        
        messages = {
            StatusType.RECORDING: "🎤 RECORDING - Press hotkey to stop",
            StatusType.PROCESSING: "⚡ PROCESSING - Transcribing audio...",
            StatusType.SUCCESS: "✅ SUCCESS - Text inserted successfully",
            StatusType.ERROR: "❌ ERROR - There was a problem with transcription"
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