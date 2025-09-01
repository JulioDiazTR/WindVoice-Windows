"""
Simple Status Dialog - Standard Tkinter version for debugging
"""

import tkinter as tk
from tkinter import Canvas
import math
from typing import Optional
from enum import Enum

class DialogState(Enum):
    RECORDING = "recording"
    PROCESSING = "processing"  
    SUCCESS = "success"
    ERROR = "error"

class SimpleStatusDialog:
    def __init__(self):
        self.window: Optional[tk.Toplevel] = None
        self.canvas: Optional[Canvas] = None
        self.is_visible = False
        self.current_state = DialogState.RECORDING
        self.animation_running = False
        self.animation_frame = 0
        self.audio_level = 0.0
        self.animation_job_id: Optional[str] = None
        
    def show(self, state: DialogState = DialogState.RECORDING):
        """Show the status dialog"""
        print(f"DEBUG: SimpleStatusDialog.show() called with state: {state}")
        
        if self.window and self.is_visible:
            self.current_state = state
            return
            
        self.current_state = state
        self._create_window()
        self._position_window()
        self.is_visible = True
        self._start_animation()
        print("DEBUG: SimpleStatusDialog should now be visible")
        
    def hide(self):
        """Hide the dialog"""
        self._stop_animation()
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
            self.canvas = None
        self.is_visible = False
        
    def _create_window(self):
        """Create a simple tkinter window"""
        print("DEBUG: Creating simple tkinter Toplevel")
        try:
            self.window = tk.Toplevel()
            self.window.title("WindVoice Status - Simple")
            self.window.geometry("150x150")
            self.window.configure(bg='black')
            self.window.attributes('-topmost', True)
            self.window.resizable(False, False)
            
            print("DEBUG: Simple window created")
            
            # Create canvas
            self.canvas = Canvas(
                self.window,
                width=140,
                height=140,
                bg='#1a1a1a',
                highlightthickness=0
            )
            self.canvas.pack(padx=5, pady=5)
            print("DEBUG: Simple canvas created")
            
        except Exception as e:
            print(f"ERROR: Failed to create simple window: {e}")
            import traceback
            traceback.print_exc()
            
    def _position_window(self):
        """Position window"""
        try:
            print("DEBUG: Positioning simple window")
            self.window.update_idletasks()
            
            screen_width = self.window.winfo_screenwidth()  
            screen_height = self.window.winfo_screenheight()
            
            x = screen_width - 200
            y = screen_height - 200
            
            self.window.geometry(f"150x150+{x}+{y}")
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            
            print(f"DEBUG: Simple window positioned at {x}, {y}")
            
        except Exception as e:
            print(f"ERROR: Could not position simple window: {e}")
            
    def _start_animation(self):
        """Start simple animation"""
        print("DEBUG: Starting simple animation")
        self.animation_running = True
        self._animate()
        
    def _stop_animation(self):
        """Stop animation"""
        self.animation_running = False
        if self.animation_job_id and self.window:
            try:
                self.window.after_cancel(self.animation_job_id)
            except:
                pass
            self.animation_job_id = None
            
    def _animate(self):
        """Simple animation"""
        if not self.animation_running or not self.canvas or not self.window:
            return
            
        try:
            self.canvas.delete("all")
            
            center_x, center_y = 70, 70
            
            if self.current_state == DialogState.RECORDING:
                # Simple pulsing red circle
                pulse = 0.8 + 0.4 * math.sin(self.animation_frame * 0.15)
                radius = int(30 * pulse)
                
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline='red', width=3, fill='darkred'
                )
                
                self.canvas.create_text(
                    center_x, center_y + 50,
                    text="RECORDING", font=('Arial', 10, 'bold'),
                    fill='red'
                )
                
            elif self.current_state == DialogState.PROCESSING:
                # Simple spinning circle
                angle = self.animation_frame * 10
                
                self.canvas.create_oval(
                    center_x - 25, center_y - 25,
                    center_x + 25, center_y + 25,
                    outline='blue', width=3, fill='darkblue'
                )
                
                # Rotating dot
                dot_x = center_x + 35 * math.cos(math.radians(angle))
                dot_y = center_y + 35 * math.sin(math.radians(angle))
                
                self.canvas.create_oval(
                    dot_x - 5, dot_y - 5,
                    dot_x + 5, dot_y + 5,
                    fill='cyan', outline=''
                )
                
                self.canvas.create_text(
                    center_x, center_y + 50,
                    text="PROCESSING", font=('Arial', 10, 'bold'),
                    fill='blue'
                )
                
            elif self.current_state == DialogState.SUCCESS:
                # Green circle with checkmark
                self.canvas.create_oval(
                    center_x - 25, center_y - 25,
                    center_x + 25, center_y + 25,
                    outline='green', width=3, fill='darkgreen'
                )
                
                # Simple checkmark
                self.canvas.create_line(
                    center_x - 10, center_y,
                    center_x - 2, center_y + 8,
                    center_x + 10, center_y - 8,
                    fill='white', width=4
                )
                
                self.canvas.create_text(
                    center_x, center_y + 50,
                    text="SUCCESS", font=('Arial', 10, 'bold'),
                    fill='green'
                )
                
                # Auto hide after 30 frames
                if self.animation_frame > 30:
                    self.window.after(100, self.hide)
                    return
                    
            elif self.current_state == DialogState.ERROR:
                # Red circle with X
                self.canvas.create_oval(
                    center_x - 25, center_y - 25,
                    center_x + 25, center_y + 25,
                    outline='red', width=3, fill='darkred'
                )
                
                # X mark
                self.canvas.create_line(
                    center_x - 10, center_y - 10,
                    center_x + 10, center_y + 10,
                    fill='white', width=4
                )
                self.canvas.create_line(
                    center_x - 10, center_y + 10,
                    center_x + 10, center_y - 10,
                    fill='white', width=4
                )
                
                self.canvas.create_text(
                    center_x, center_y + 50,
                    text="ERROR", font=('Arial', 10, 'bold'),
                    fill='red'
                )
                
                # Auto hide after 40 frames
                if self.animation_frame > 40:
                    self.window.after(100, self.hide)
                    return
            
            self.animation_frame += 1
            
            if self.animation_running and self.window:
                self.animation_job_id = self.window.after(50, self._animate)
                
        except Exception as e:
            print(f"Animation error: {e}")
            self.animation_running = False
            
    def update_audio_level(self, level: float):
        """Update audio level"""
        self.audio_level = min(1.0, max(0.0, level))


class SimpleStatusDialogManager:
    """Simple manager for the status dialog"""
    
    def __init__(self):
        self.dialog: Optional[SimpleStatusDialog] = None
        
    def show_recording(self):
        print("DEBUG: SimpleStatusDialogManager.show_recording() called")
        if not self.dialog:
            print("DEBUG: Creating new SimpleStatusDialog")  
            self.dialog = SimpleStatusDialog()
        print("DEBUG: Showing recording state")
        self.dialog.show(DialogState.RECORDING)
        
    def show_processing(self):
        if self.dialog:
            self.dialog.current_state = DialogState.PROCESSING
        else:
            self.dialog = SimpleStatusDialog()
            self.dialog.show(DialogState.PROCESSING)
            
    def show_success(self):
        if self.dialog:
            self.dialog.current_state = DialogState.SUCCESS
        else:
            self.dialog = SimpleStatusDialog()
            self.dialog.show(DialogState.SUCCESS)
            
    def show_error(self):
        if self.dialog:
            self.dialog.current_state = DialogState.ERROR
        else:
            self.dialog = SimpleStatusDialog()
            self.dialog.show(DialogState.ERROR)
            
    def update_audio_level(self, level: float):
        if self.dialog:
            self.dialog.update_audio_level(level)
            
    def hide(self):
        if self.dialog:
            self.dialog.hide()
            self.dialog = None
            
    def is_visible(self) -> bool:
        return self.dialog is not None and self.dialog.is_visible