"""
Robust Status Dialog Implementation
Using best practices for reliable window visibility across Windows systems.
"""

import tkinter as tk
from tkinter import Canvas
import customtkinter as ctk
import math
import threading
import time
from typing import Optional, Callable
from enum import Enum


class StatusState(Enum):
    """Status dialog states"""
    RECORDING = "recording"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


class RobustStatusDialog:
    """
    Robust status dialog with guaranteed visibility using multiple fallback approaches.
    """
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        self.parent_window = parent_window
        self.window: Optional[tk.Toplevel] = None  # Use standard Tkinter for reliability
        self.canvas: Optional[Canvas] = None
        self.is_visible = False
        self.current_state = StatusState.RECORDING
        self.animation_running = False
        self.animation_frame = 0
        self.animation_job_id: Optional[str] = None
        self.audio_level = 0.0
        
        # Window positioning
        self.window_width = 150
        self.window_height = 150
        
    def show(self, state: StatusState = StatusState.RECORDING):
        """Show the status dialog with guaranteed visibility"""
        print(f"RobustStatusDialog: Showing state {state}")
        
        # Hide existing window first
        if self.is_visible:
            self.hide()
            
        self.current_state = state
        
        try:
            self._create_window()
            self._ensure_visibility()
            self.is_visible = True
            self._start_animation()
            print("RobustStatusDialog: Successfully shown")
            
        except Exception as e:
            print(f"RobustStatusDialog ERROR: Failed to show dialog: {e}")
            import traceback
            traceback.print_exc()
            
    def hide(self):
        """Hide the status dialog"""
        print("RobustStatusDialog: Hiding dialog")
        self._stop_animation()
        
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
            self.canvas = None
            
        self.is_visible = False
        
    def update_audio_level(self, level: float):
        """Update audio level for recording visualization"""
        self.audio_level = max(0.0, min(1.0, level))
        
    def _create_window(self):
        """Create the status window using standard Tkinter for maximum compatibility"""
        print("RobustStatusDialog: Creating window...")
        
        # Use standard Tkinter Toplevel for maximum compatibility
        if self.parent_window:
            self.window = tk.Toplevel(self.parent_window)
        else:
            # Create a temporary root if none exists
            root = tk.Tk()
            root.withdraw()
            self.window = tk.Toplevel(root)
            
        # Configure window
        self.window.title("WindVoice Status")
        self.window.geometry(f"{self.window_width}x{self.window_height}")
        self.window.resizable(False, False)
        
        # Make window always on top and visible
        self.window.attributes("-topmost", True)
        self.window.attributes("-toolwindow", True)  # Windows-specific: prevent taskbar icon
        
        # Modern dark styling
        self.window.configure(bg='#1a1a1a')
        
        # Remove window decorations for modern look
        self.window.overrideredirect(True)
        
        # Create canvas for animations
        self.canvas = Canvas(
            self.window,
            width=self.window_width-10,
            height=self.window_height-10,
            bg='#1a1a1a',
            highlightthickness=0,
            relief='flat'
        )
        self.canvas.pack(padx=5, pady=5)
        
        # Add border for better visibility
        self.canvas.create_rectangle(
            0, 0, self.window_width-10, self.window_height-10,
            outline='#444444', width=2, fill=''
        )
        
        print("RobustStatusDialog: Window created successfully")
        
    def _ensure_visibility(self):
        """Ensure the window is actually visible using multiple methods"""
        print("RobustStatusDialog: Ensuring visibility...")
        
        if not self.window:
            return
            
        try:
            # Method 1: Position window
            self._position_window()
            
            # Method 2: Force window to appear
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            
            # Method 3: Update and flush events
            self.window.update_idletasks()
            self.window.update()
            
            # Method 4: Force redraw
            if self.canvas:
                self.canvas.update_idletasks()
                self.canvas.update()
                
            # Method 5: Windows-specific visibility fixes
            try:
                import ctypes
                from ctypes import wintypes
                
                # Get window handle
                hwnd = self.window.winfo_id()
                
                # Force window to be visible and on top
                SWP_SHOWWINDOW = 0x0040
                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002
                HWND_TOPMOST = -1
                
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                )
                
                print("RobustStatusDialog: Applied Windows-specific visibility fixes")
                
            except Exception as e:
                print(f"RobustStatusDialog: Windows-specific fixes failed (not critical): {e}")
                
            print("RobustStatusDialog: Visibility ensured")
            
        except Exception as e:
            print(f"RobustStatusDialog ERROR: Failed to ensure visibility: {e}")
            raise
            
    def _position_window(self):
        """Position window in bottom-right corner"""
        try:
            # Get screen dimensions
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # Calculate position (bottom-right with margin)
            margin = 50
            x = screen_width - self.window_width - margin
            y = screen_height - self.window_height - margin
            
            # Set position
            self.window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
            print(f"RobustStatusDialog: Positioned at ({x}, {y})")
            
        except Exception as e:
            print(f"RobustStatusDialog: Positioning failed, using default: {e}")
            self.window.geometry(f"{self.window_width}x{self.window_height}+100+100")
            
    def _start_animation(self):
        """Start animation loop"""
        self.animation_running = True
        self.animation_frame = 0
        self._animate()
        
    def _stop_animation(self):
        """Stop animation loop"""
        self.animation_running = False
        if self.animation_job_id and self.window:
            try:
                self.window.after_cancel(self.animation_job_id)
            except:
                pass
            self.animation_job_id = None
            
    def _animate(self):
        """Animation loop with simple, reliable graphics"""
        if not self.animation_running or not self.canvas or not self.window:
            return
            
        try:
            # Clear canvas
            self.canvas.delete("animation")
            
            # Draw border
            self.canvas.create_rectangle(
                0, 0, self.window_width-10, self.window_height-10,
                outline='#444444', width=2, fill='', tags="animation"
            )
            
            center_x, center_y = (self.window_width-10)//2, (self.window_height-10)//2
            
            # Simple, reliable animations
            if self.current_state == StatusState.RECORDING:
                self._draw_recording_simple(center_x, center_y)
            elif self.current_state == StatusState.PROCESSING:
                self._draw_processing_simple(center_x, center_y)
            elif self.current_state == StatusState.SUCCESS:
                self._draw_success_simple(center_x, center_y)
            elif self.current_state == StatusState.ERROR:
                self._draw_error_simple(center_x, center_y)
                
            self.animation_frame += 1
            
            # Schedule next frame
            if self.animation_running and self.window:
                self.animation_job_id = self.window.after(100, self._animate)  # 10 FPS for reliability
                
        except Exception as e:
            print(f"RobustStatusDialog: Animation error: {e}")
            self.animation_running = False
            
    def _draw_recording_simple(self, center_x: int, center_y: int):
        """Simple recording animation"""
        # Pulsing red circle
        pulse = 0.8 + 0.4 * math.sin(self.animation_frame * 0.2)
        radius = int(20 + 10 * pulse)
        
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline='red', width=3, fill='darkred', tags="animation"
        )
        
        # Simple text
        self.canvas.create_text(
            center_x, center_y + 50,
            text="GRABANDO", font=('Arial', 10, 'bold'),
            fill='red', tags="animation"
        )
        
    def _draw_processing_simple(self, center_x: int, center_y: int):
        """Simple processing animation"""
        # Rotating circle
        angle = self.animation_frame * 10
        
        self.canvas.create_oval(
            center_x - 25, center_y - 25,
            center_x + 25, center_y + 25,
            outline='blue', width=3, fill='darkblue', tags="animation"
        )
        
        # Rotating dot
        dot_x = center_x + 30 * math.cos(math.radians(angle))
        dot_y = center_y + 30 * math.sin(math.radians(angle))
        
        self.canvas.create_oval(
            dot_x - 5, dot_y - 5,
            dot_x + 5, dot_y + 5,
            fill='cyan', outline='', tags="animation"
        )
        
        # Simple text
        self.canvas.create_text(
            center_x, center_y + 50,
            text="PROCESANDO", font=('Arial', 10, 'bold'),
            fill='blue', tags="animation"
        )
        
    def _draw_success_simple(self, center_x: int, center_y: int):
        """Simple success animation"""
        # Green circle
        self.canvas.create_oval(
            center_x - 25, center_y - 25,
            center_x + 25, center_y + 25,
            outline='green', width=3, fill='darkgreen', tags="animation"
        )
        
        # Simple checkmark
        self.canvas.create_line(
            center_x - 10, center_y,
            center_x - 2, center_y + 8,
            center_x + 10, center_y - 8,
            fill='white', width=4, tags="animation"
        )
        
        # Simple text
        self.canvas.create_text(
            center_x, center_y + 50,
            text="ÉXITO", font=('Arial', 10, 'bold'),
            fill='green', tags="animation"
        )
        
        # Auto-hide after 2 seconds
        if self.animation_frame > 20:
            threading.Timer(0.5, self.hide).start()
            
    def _draw_error_simple(self, center_x: int, center_y: int):
        """Simple error animation"""
        # Red circle
        self.canvas.create_oval(
            center_x - 25, center_y - 25,
            center_x + 25, center_y + 25,
            outline='red', width=3, fill='darkred', tags="animation"
        )
        
        # Simple X
        self.canvas.create_line(
            center_x - 10, center_y - 10,
            center_x + 10, center_y + 10,
            fill='white', width=4, tags="animation"
        )
        self.canvas.create_line(
            center_x - 10, center_y + 10,
            center_x + 10, center_y - 10,
            fill='white', width=4, tags="animation"
        )
        
        # Simple text
        self.canvas.create_text(
            center_x, center_y + 50,
            text="ERROR", font=('Arial', 10, 'bold'),
            fill='red', tags="animation"
        )
        
        # Auto-hide after 3 seconds
        if self.animation_frame > 30:
            threading.Timer(0.5, self.hide).start()


class RobustStatusDialogManager:
    """Manager for robust status dialog"""
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        self.parent_window = parent_window
        self.dialog: Optional[RobustStatusDialog] = None
        
    def show_recording(self):
        """Show recording state"""
        print("RobustStatusDialogManager: show_recording() called")
        if not self.dialog:
            self.dialog = RobustStatusDialog(self.parent_window)
        self.dialog.show(StatusState.RECORDING)
        
    def show_processing(self):
        """Show processing state"""
        print("RobustStatusDialogManager: show_processing() called")
        if not self.dialog:
            self.dialog = RobustStatusDialog(self.parent_window)
        self.dialog.show(StatusState.PROCESSING)
        
    def show_success(self):
        """Show success state"""
        print("RobustStatusDialogManager: show_success() called")
        if not self.dialog:
            self.dialog = RobustStatusDialog(self.parent_window)
        self.dialog.show(StatusState.SUCCESS)
        
    def show_error(self):
        """Show error state"""
        print("RobustStatusDialogManager: show_error() called")
        if not self.dialog:
            self.dialog = RobustStatusDialog(self.parent_window)
        self.dialog.show(StatusState.ERROR)
        
    def update_audio_level(self, level: float):
        """Update audio level"""
        if self.dialog:
            self.dialog.update_audio_level(level)
            
    def hide(self):
        """Hide dialog"""
        if self.dialog:
            self.dialog.hide()
            self.dialog = None
            
    def is_visible(self) -> bool:
        """Check if dialog is visible"""
        return self.dialog is not None and self.dialog.is_visible


# Test function
def test_robust_dialog():
    """Test the robust dialog implementation"""
    print("Testing Robust Status Dialog...")
    
    root = tk.Tk()
    root.withdraw()  # Hide root
    
    manager = RobustStatusDialogManager(root)
    
    # Test sequence
    def test_sequence():
        print("Starting test sequence...")
        
        # Recording
        manager.show_recording()
        time.sleep(3)
        
        # Processing
        manager.show_processing()
        time.sleep(3)
        
        # Success
        manager.show_success()
        time.sleep(3)
        
        # Error
        manager.show_error()
        time.sleep(4)
        
        # Quit
        root.quit()
        
    threading.Thread(target=test_sequence, daemon=True).start()
    root.mainloop()
    

if __name__ == "__main__":
    test_robust_dialog()