"""
WindVoice Status Dialog

Transparent dialog with visual feedback animations for recording and processing states.
Replaces slow system tray notifications with fast, smooth visual feedback.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import Canvas
import math
from typing import Optional, Callable, Literal
from enum import Enum

class DialogState(Enum):
    """Dialog states with different animations"""
    RECORDING = "recording"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"

class StatusDialog:
    def __init__(self, parent_window: Optional[tk.Tk] = None, on_close: Optional[Callable] = None):
        self.parent_window = parent_window
        self.on_close = on_close
        self.window: Optional[ctk.CTkToplevel] = None
        self.canvas: Optional[Canvas] = None
        self.is_visible = False
        self.current_state = DialogState.RECORDING
        self.animation_running = False
        self.animation_frame = 0
        self.audio_level = 0.0
        self.animation_job_id: Optional[str] = None
        
        # Animation parameters
        self.pulse_speed = 0.15
        self.wave_speed = 0.2
        self.processing_dots = 0
        
    def show(self, state: DialogState = DialogState.RECORDING):
        """Show the status dialog in the specified state"""
        print(f"DEBUG: StatusDialog.show() called with state: {state}")
        
        if self.window and self.is_visible:
            print("DEBUG: Window already exists and is visible, just changing state")
            self.set_state(state)
            return
            
        print("DEBUG: Creating new window...")
        self.current_state = state
        self._create_window()
        self._position_window()
        self.is_visible = True
        self._start_animation()
        print("DEBUG: StatusDialog should now be visible")
        
    def hide(self):
        """Hide the status dialog"""
        self._stop_animation()
        
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
            self.canvas = None
            
        self.is_visible = False
        
        if self.on_close:
            self.on_close()
    
    def set_state(self, state: DialogState):
        """Change dialog state and update animation"""
        self.current_state = state
        if state == DialogState.PROCESSING:
            self.processing_dots = 0
        
    def update_audio_level(self, level: float):
        """Update audio level for recording visualization (0.0 to 1.0)"""
        self.audio_level = min(1.0, max(0.0, level))
    
    def _create_window(self):
        """Create the modern transparent status window"""
        print(f"DEBUG: StatusDialog._create_window() called, parent_window={self.parent_window}")
        try:
            # Use parent window if available, otherwise create standalone
            if self.parent_window:
                print(f"DEBUG: Creating CTkToplevel with parent: {self.parent_window}")
                self.window = ctk.CTkToplevel(self.parent_window)
            else:
                print("DEBUG: Creating CTkToplevel without parent")
                self.window = ctk.CTkToplevel()
            
            print(f"DEBUG: CTkToplevel created successfully: {self.window}")
            self.window.title("WindVoice Status")
            
            # Make window modern and transparent
            window_size = 120
            self.window.geometry(f"{window_size}x{window_size}")
            self.window.resizable(False, False)
            self.window.attributes("-topmost", True)
            self.window.attributes("-alpha", 0.85)  # More transparent
            self.window.overrideredirect(True)  # Remove window decorations
            print("DEBUG: Window configuration completed")
            
        except Exception as e:
            print(f"ERROR: Failed to create status window: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Try to add Windows 11 style effects (if available)
        try:
            # Windows 11 acrylic/blur effect
            import ctypes
            from ctypes import wintypes
            hwnd = self.window.winfo_id()
            # Enable blur behind effect
            ctypes.windll.dwmapi.DwmEnableBlurBehindWindow(hwnd, ctypes.byref(ctypes.c_int(1)))
        except:
            pass  # Fallback gracefully if not available
        
        # Create main container frame with glassmorphism styling
        self.main_frame = ctk.CTkFrame(
            self.window,
            width=window_size,
            height=window_size,
            corner_radius=30,  # More rounded for modern look
            fg_color=("rgba(20, 20, 20, 0.7)", "rgba(20, 20, 20, 0.7)"),  # Glassmorphism effect
            border_width=1,
            border_color=("rgba(255, 255, 255, 0.1)", "rgba(255, 255, 255, 0.1)")
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Create canvas for animations with transparent styling
        self.canvas = Canvas(
            self.main_frame, 
            width=window_size-8, 
            height=window_size-8,
            bg='#141414',  # Slightly lighter dark background
            highlightthickness=0,
            relief='flat'
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Enhanced dragging - bind to both canvas and frame
        self.canvas.bind("<Button-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self.main_frame.bind("<Button-1>", self._on_drag_start)
        self.main_frame.bind("<B1-Motion>", self._on_drag_motion)
        self.main_frame.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Right click menu
        self.canvas.bind("<Button-3>", self._show_context_menu)
        self.main_frame.bind("<Button-3>", self._show_context_menu)
        
        # Hover effects
        self.canvas.bind("<Enter>", self._on_hover_enter)
        self.canvas.bind("<Leave>", self._on_hover_leave)
        
        # Add subtle drop shadow effect
        self._add_drop_shadow_effect()
        
        # Dragging state
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
    def _position_window(self):
        """Position window near cursor on active monitor with smart placement"""
        try:
            self.window.update_idletasks()
            
            # Get cursor position and active monitor
            cursor_x, cursor_y = self._get_cursor_position()
            monitor_info = self._get_active_monitor(cursor_x, cursor_y)
            
            # Window size
            window_size = 120
            margin = 50  # Distance from cursor
            
            # Smart positioning near cursor but not covering it
            # Try positioning to bottom-right of cursor first
            x = cursor_x + margin
            y = cursor_y + margin
            
            # Ensure window stays within monitor bounds
            if x + window_size > monitor_info['right']:
                x = cursor_x - window_size - margin  # Move to left of cursor
            if y + window_size > monitor_info['bottom']:
                y = cursor_y - window_size - margin  # Move above cursor
                
            # Final bounds check
            x = max(monitor_info['left'], min(x, monitor_info['right'] - window_size))
            y = max(monitor_info['top'], min(y, monitor_info['bottom'] - window_size))
            
            # Apply position
            self.window.geometry(f"{window_size}x{window_size}+{x}+{y}")
            self.window.deiconify()
            self.window.lift()
            
        except Exception as e:
            print(f"Could not position status dialog: {e}")
            # Fallback to simple cursor-based positioning
            try:
                cursor_x, cursor_y = self._get_cursor_position()
                fallback_x = max(50, cursor_x - 60)
                fallback_y = max(50, cursor_y + 50)
                self.window.geometry(f"120x120+{fallback_x}+{fallback_y}")
            except:
                self.window.geometry(f"120x120+100+100")
    
    def _get_cursor_position(self):
        """Get current cursor position"""
        try:
            import win32gui
            return win32gui.GetCursorPos()
        except ImportError:
            # Fallback using tkinter
            try:
                self.window.update_idletasks()
                return self.window.winfo_pointerx(), self.window.winfo_pointery()
            except:
                return 200, 200  # Default position
    
    def _get_active_monitor(self, cursor_x, cursor_y):
        """Get information about the monitor containing the cursor"""
        try:
            import win32api
            import win32con
            
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
            self.window.update_idletasks()
            width = self.window.winfo_screenwidth()
            height = self.window.winfo_screenheight()
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
    
    def _add_drop_shadow_effect(self):
        """Add drop shadow effect to window"""
        try:
            # Try to add Windows drop shadow effect
            import ctypes
            from ctypes import wintypes
            
            # Get window handle
            hwnd = self.window.winfo_id()
            
            # Apply drop shadow effect
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            
            # Get current extended window style
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            # Add layered window style for effects
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
            
        except:
            pass  # Fallback gracefully
    
    def _show_context_menu(self, event):
        """Show context menu on right click"""
        try:
            import tkinter.ttk as ttk
            
            # Create context menu
            context_menu = tk.Menu(self.window, tearoff=0)
            context_menu.add_command(label="📌 Stay on Top", command=self._toggle_topmost)
            context_menu.add_separator()
            context_menu.add_command(label="🎨 Change Transparency", command=self._cycle_transparency)
            context_menu.add_separator()
            context_menu.add_command(label="❌ Hide", command=self.hide)
            
            # Show menu at cursor position
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
                
        except Exception as e:
            print(f"Context menu error: {e}")
    
    def _toggle_topmost(self):
        """Toggle always on top"""
        if self.window:
            current = self.window.attributes("-topmost")
            self.window.attributes("-topmost", not current)
    
    def _cycle_transparency(self):
        """Cycle through transparency levels"""
        if self.window:
            current_alpha = self.window.attributes("-alpha")
            transparencies = [0.6, 0.75, 0.85, 0.95, 1.0]  # More transparent options
            
            # Find next transparency level
            try:
                current_index = transparencies.index(current_alpha)
                next_index = (current_index + 1) % len(transparencies)
            except ValueError:
                next_index = 0
                
            self.window.attributes("-alpha", transparencies[next_index])
    
    def _on_hover_enter(self, event):
        """Handle mouse hover enter"""
        if self.window and not self.dragging:
            # Slightly increase opacity on hover
            current_alpha = self.window.attributes("-alpha")
            if current_alpha < 1.0:
                self.window.attributes("-alpha", min(1.0, current_alpha + 0.1))
    
    def _on_hover_leave(self, event):
        """Handle mouse hover leave"""
        if self.window and not self.dragging:
            # Restore original opacity
            self.window.attributes("-alpha", 0.85)
    
    def _start_animation(self):
        """Start the animation loop using Tkinter's after method"""
        self.animation_running = True
        self._animate()
    
    def _stop_animation(self):
        """Stop the animation loop"""
        self.animation_running = False
        if self.animation_job_id and self.window:
            try:
                self.window.after_cancel(self.animation_job_id)
            except:
                pass
            self.animation_job_id = None
    
    def _animate(self):
        """Main animation loop using Tkinter's after method"""
        if not self.animation_running or not self.canvas or not self.window:
            return
            
        try:
            self.canvas.delete("all")  # Clear canvas
            
            center_x, center_y = 60, 60
            
            if self.current_state == DialogState.RECORDING:
                self._draw_recording_animation(center_x, center_y)
            elif self.current_state == DialogState.PROCESSING:
                self._draw_processing_animation(center_x, center_y)
            elif self.current_state == DialogState.SUCCESS:
                self._draw_success_animation(center_x, center_y)
            elif self.current_state == DialogState.ERROR:
                self._draw_error_animation(center_x, center_y)
            
            self.animation_frame += 1
            
            # Schedule next frame using Tkinter's after method
            if self.animation_running and self.window:
                self.animation_job_id = self.window.after(50, self._animate)  # 20 FPS
                
        except Exception as e:
            print(f"Animation error: {e}")
            self.animation_running = False
    
    def _draw_recording_animation(self, center_x: int, center_y: int):
        """Draw modern recording animation with audio level visualization"""
        # Animated gradient-like effect with multiple rings
        pulse = 0.7 + 0.4 * math.sin(self.animation_frame * self.pulse_speed)
        
        # Draw multiple concentric circles for depth effect
        for ring in range(4):
            radius = 15 + ring * 8 + (self.audio_level * 20) * pulse * (1 - ring * 0.2)
            opacity = max(20, int(255 * (1 - ring * 0.25) * (0.5 + self.audio_level * 0.5)))
            
            # Color gradient from bright red to dark red
            red_intensity = max(100, int(255 - ring * 30))
            color = f"#{red_intensity:02x}{max(0, red_intensity-100):02x}{max(0, red_intensity-200):02x}"
            
            # Create ring with varying thickness
            ring_width = max(1, 4 - ring)
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=color, width=ring_width, fill=""
            )
        
        # Central microphone with modern design
        mic_radius = 12
        
        # Microphone background glow
        self.canvas.create_oval(
            center_x - mic_radius - 2, center_y - mic_radius - 2,
            center_x + mic_radius + 2, center_y + mic_radius + 2,
            fill="#ff4444", outline=""
        )
        
        # Microphone main body
        self.canvas.create_oval(
            center_x - mic_radius, center_y - mic_radius,
            center_x + mic_radius, center_y + mic_radius,
            fill="#cc0000", outline="#ff6666", width=2
        )
        
        # Modern microphone icon with better design
        self._create_rounded_rectangle(
            center_x - 5, center_y - 8,
            center_x + 5, center_y + 1,
            radius=3, fill="white", outline=""
        )
        
        # Microphone base
        self._create_rounded_rectangle(
            center_x - 7, center_y + 1,
            center_x + 7, center_y + 4,
            radius=2, fill="white", outline=""
        )
        
        # Microphone stand
        self.canvas.create_line(
            center_x, center_y + 4,
            center_x, center_y + 8,
            fill="white", width=2
        )
        
        # Dynamic audio level visualization
        if self.audio_level > 0.05:
            self._draw_audio_waveform(center_x, center_y)
        
        # Modern recording indicator with glow effect
        text_glow = "#ff8888" if int(self.animation_frame / 10) % 2 else "#ff4444"
        self.canvas.create_text(
            center_x + 1, center_y + 45,
            text="REC", font=("Segoe UI", 10, "bold"),
            fill="#444444"  # Shadow
        )
        self.canvas.create_text(
            center_x, center_y + 44,
            text="REC", font=("Segoe UI", 10, "bold"),
            fill=text_glow
        )
    
    def _draw_audio_waveform(self, center_x: int, center_y: int):
        """Draw dynamic audio waveform around microphone"""
        wave_radius = 45
        wave_points = 16
        
        for i in range(wave_points):
            angle = i * (360 / wave_points) + self.animation_frame * 2
            
            # Create wave effect based on audio level
            wave_amplitude = 3 + self.audio_level * 8
            wave_offset = wave_amplitude * math.sin(self.animation_frame * 0.3 + i * 0.5)
            
            current_radius = wave_radius + wave_offset
            x = center_x + current_radius * math.cos(math.radians(angle))
            y = center_y + current_radius * math.sin(math.radians(angle))
            
            # Color based on audio level and position
            intensity = max(0, min(255, int(100 + self.audio_level * 155)))
            half_intensity = max(0, min(255, intensity // 2))
            
            # Draw wave point
            point_size = max(1, 1 + int(self.audio_level * 2))
            self.canvas.create_oval(
                x - point_size, y - point_size,
                x + point_size, y + point_size,
                fill=f"#ff{intensity:02x}{half_intensity:02x}", outline=""
            )
    
    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=5, **kwargs):
        """Helper method to create rounded rectangles"""
        if not self.canvas:
            return
            
        # Create a simple rectangle as fallback for rounded corners
        # (Tkinter Canvas doesn't have native rounded rectangle support)
        return self.canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
    
    def _draw_processing_animation(self, center_x: int, center_y: int):
        """Draw modern processing animation with neural network effect"""
        # Rotating wave effect
        angle_offset = self.animation_frame * self.wave_speed * 8
        
        # Multiple concentric processing rings
        for ring in range(3):
            radius = 20 + ring * 10
            ring_angle = angle_offset + ring * 30
            
            # Create flowing circle segments
            segments = 6
            for seg in range(segments):
                start_angle = seg * (360 / segments) + ring_angle
                extent = 45  # Arc length
                
                # Color gradient from cyan to blue
                blue_intensity = 150 + int(50 * math.sin(self.animation_frame * 0.1 + ring))
                cyan_intensity = 100 + int(100 * math.sin(self.animation_frame * 0.15 + seg))
                color = f"#{0:02x}{cyan_intensity:02x}{blue_intensity:02x}"
                
                # Draw arc segment
                self.canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=start_angle, extent=extent,
                    outline=color, width=3 - ring, style="arc"
                )
        
        # Central processing core with pulsing effect
        core_pulse = 0.8 + 0.3 * math.sin(self.animation_frame * 0.2)
        core_radius = int(12 * core_pulse)
        
        # Core glow effect
        self.canvas.create_oval(
            center_x - core_radius - 3, center_y - core_radius - 3,
            center_x + core_radius + 3, center_y + core_radius + 3,
            fill="#004466", outline=""
        )
        
        # Main core
        self.canvas.create_oval(
            center_x - core_radius, center_y - core_radius,
            center_x + core_radius, center_y + core_radius,
            fill="#0088cc", outline="#00aaff", width=2
        )
        
        # Neural network nodes effect
        self._draw_neural_network(center_x, center_y)
        
        # AI processing icon
        brain_size = 6
        self.canvas.create_oval(
            center_x - brain_size, center_y - brain_size,
            center_x + brain_size, center_y + brain_size,
            fill="white", outline=""
        )
        
        # Brain pattern
        self.canvas.create_arc(
            center_x - 4, center_y - 4,
            center_x + 4, center_y + 4,
            start=0, extent=180, outline="#0066aa", width=2
        )
        self.canvas.create_arc(
            center_x - 4, center_y - 4,
            center_x + 4, center_y + 4,
            start=180, extent=180, outline="#0066aa", width=2
        )
        
        # Modern processing text with glow
        processing_text = "AI PROCESSING"
        dots = "." * ((self.animation_frame // 8) % 4)
        
        # Text shadow
        self.canvas.create_text(
            center_x + 1, center_y + 45,
            text=processing_text + dots, font=("Segoe UI", 8, "bold"),
            fill="#333333"
        )
        # Main text with glow
        text_color = "#0088ff" if int(self.animation_frame / 15) % 2 else "#00aaff"
        self.canvas.create_text(
            center_x, center_y + 44,
            text=processing_text + dots, font=("Segoe UI", 8, "bold"),
            fill=text_color
        )
    
    def _draw_neural_network(self, center_x: int, center_y: int):
        """Draw neural network connection effect"""
        node_radius = 35
        node_count = 6
        
        # Draw connecting lines between nodes
        for i in range(node_count):
            angle1 = i * (360 / node_count) + self.animation_frame * 2
            x1 = center_x + node_radius * math.cos(math.radians(angle1))
            y1 = center_y + node_radius * math.sin(math.radians(angle1))
            
            # Connect to next 2 nodes
            for j in range(1, 3):
                next_i = (i + j) % node_count
                angle2 = next_i * (360 / node_count) + self.animation_frame * 2
                x2 = center_x + node_radius * math.cos(math.radians(angle2))
                y2 = center_y + node_radius * math.sin(math.radians(angle2))
                
                # Animated connection strength
                alpha = int(50 + 100 * abs(math.sin(self.animation_frame * 0.1 + i + j)))
                alpha = max(0, min(255, alpha))  # Clamp to valid range
                blue_intensity = max(0, min(255, alpha + 50))
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=f"#{0:02x}{alpha:02x}{blue_intensity:02x}",
                    width=1
                )
        
        # Draw neural network nodes
        for i in range(node_count):
            angle = i * (360 / node_count) + self.animation_frame * 2
            x = center_x + node_radius * math.cos(math.radians(angle))
            y = center_y + node_radius * math.sin(math.radians(angle))
            
            # Node pulse effect
            pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.15 + i)
            node_size = int(2 + pulse * 2)
            
            self.canvas.create_oval(
                x - node_size, y - node_size,
                x + node_size, y + node_size,
                fill="#00ccff", outline=""
            )
    
    def _draw_success_animation(self, center_x: int, center_y: int):
        """Draw modern success animation with expanding checkmark"""
        # Animated expanding success circle
        expand_progress = min(1.0, self.animation_frame / 10.0)
        base_radius = int(25 * expand_progress)
        
        # Multiple success rings with glow effect
        for ring in range(3):
            radius = base_radius + ring * 5
            alpha = max(0, 255 - ring * 80)
            green_intensity = max(100, 255 - ring * 40)
            
            # Outer glow
            if ring == 0:
                self.canvas.create_oval(
                    center_x - radius - 5, center_y - radius - 5,
                    center_x + radius + 5, center_y + radius + 5,
                    fill="#004400", outline=""
                )
            
            # Main success circle
            color = f"#{0:02x}{green_intensity:02x}{0:02x}"
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill=color if ring == 2 else "",
                outline=color, width=3 - ring
            )
        
        # Animated checkmark with smooth drawing
        if expand_progress > 0.3:
            checkmark_progress = min(1.0, (self.animation_frame - 6) / 8.0)
            
            # Checkmark background glow
            self.canvas.create_oval(
                center_x - 15, center_y - 15,
                center_x + 15, center_y + 15,
                fill="#00aa00", outline=""
            )
            
            # Progressive checkmark drawing
            if checkmark_progress > 0:
                # First stroke (left part of checkmark)
                stroke1_progress = min(1.0, checkmark_progress * 2)
                end_x1 = center_x - 8 + (6 * stroke1_progress)
                end_y1 = center_y + (6 * stroke1_progress)
                
                self.canvas.create_line(
                    center_x - 8, center_y,
                    end_x1, end_y1,
                    fill="white", width=4, capstyle="round"
                )
                
                # Second stroke (right part of checkmark)
                if checkmark_progress > 0.5:
                    stroke2_progress = min(1.0, (checkmark_progress - 0.5) * 2)
                    end_x2 = center_x - 2 + (10 * stroke2_progress)
                    end_y2 = center_y + 6 - (12 * stroke2_progress)
                    
                    self.canvas.create_line(
                        center_x - 2, center_y + 6,
                        end_x2, end_y2,
                        fill="white", width=4, capstyle="round"
                    )
        
        # Sparkle effects around success
        if expand_progress > 0.7:
            self._draw_success_sparkles(center_x, center_y)
        
        # Modern success text with glow
        if expand_progress > 0.5:
            # Text shadow
            self.canvas.create_text(
                center_x + 1, center_y + 45,
                text="SUCCESS", font=("Segoe UI", 9, "bold"),
                fill="#004400"
            )
            # Main text
            self.canvas.create_text(
                center_x, center_y + 44,
                text="SUCCESS", font=("Segoe UI", 9, "bold"),
                fill="#00cc00"
            )
        
        # Auto-hide after 1.5 seconds
        if self.animation_frame > 30:  # ~1.5 seconds at 20 FPS
            if self.window:
                self.window.after(100, self.hide)
    
    def _draw_success_sparkles(self, center_x: int, center_y: int):
        """Draw sparkle effects around success animation"""
        sparkle_count = 6
        for i in range(sparkle_count):
            angle = i * (360 / sparkle_count) + self.animation_frame * 5
            distance = 40 + 10 * math.sin(self.animation_frame * 0.2 + i)
            
            x = center_x + distance * math.cos(math.radians(angle))
            y = center_y + distance * math.sin(math.radians(angle))
            
            # Sparkle size varies with time
            sparkle_size = 2 + int(2 * math.sin(self.animation_frame * 0.3 + i))
            
            # Draw star-like sparkle
            self.canvas.create_oval(
                x - sparkle_size, y - sparkle_size,
                x + sparkle_size, y + sparkle_size,
                fill="#ffffff", outline=""
            )
            # Smaller inner sparkle
            inner_size = max(1, sparkle_size - 1)
            self.canvas.create_oval(
                x - inner_size, y - inner_size,
                x + inner_size, y + inner_size,
                fill="#ffff00", outline=""
            )
    
    def _draw_error_animation(self, center_x: int, center_y: int):
        """Draw modern error animation with shake effect and X mark"""
        # Shake effect for error
        shake_intensity = max(0, 5 - (self.animation_frame // 5))
        shake_x = int(shake_intensity * math.sin(self.animation_frame * 0.8))
        shake_y = int(shake_intensity * math.cos(self.animation_frame * 0.6))
        
        actual_center_x = center_x + shake_x
        actual_center_y = center_y + shake_y
        
        # Animated expanding error circle
        expand_progress = min(1.0, self.animation_frame / 8.0)
        base_radius = int(25 * expand_progress)
        
        # Warning pulsing outer rings
        pulse = 0.8 + 0.4 * math.sin(self.animation_frame * 0.4)
        
        for ring in range(3):
            radius = (base_radius + ring * 4) * pulse
            red_intensity = max(150, 255 - ring * 30)
            
            # Outer warning glow
            if ring == 0:
                self.canvas.create_oval(
                    actual_center_x - radius - 5, actual_center_y - radius - 5,
                    actual_center_x + radius + 5, actual_center_y + radius + 5,
                    fill="#440000", outline=""
                )
            
            # Main error circles
            color = f"#{red_intensity:02x}{0:02x}{0:02x}"
            self.canvas.create_oval(
                actual_center_x - radius, actual_center_y - radius,
                actual_center_x + radius, actual_center_y + radius,
                fill=color if ring == 2 else "",
                outline=color, width=3 - ring
            )
        
        # Animated X mark with progressive drawing
        if expand_progress > 0.3:
            x_progress = min(1.0, (self.animation_frame - 6) / 10.0)
            
            # X mark background
            self.canvas.create_oval(
                actual_center_x - 15, actual_center_y - 15,
                actual_center_x + 15, actual_center_y + 15,
                fill="#cc0000", outline=""
            )
            
            # Progressive X drawing
            if x_progress > 0:
                # First diagonal (top-left to bottom-right)
                stroke1_progress = min(1.0, x_progress * 1.5)
                end_x1 = actual_center_x - 8 + (16 * stroke1_progress)
                end_y1 = actual_center_y - 8 + (16 * stroke1_progress)
                
                self.canvas.create_line(
                    actual_center_x - 8, actual_center_y - 8,
                    end_x1, end_y1,
                    fill="white", width=5, capstyle="round"
                )
                
                # Second diagonal (top-right to bottom-left)  
                if x_progress > 0.3:
                    stroke2_progress = min(1.0, (x_progress - 0.3) * 1.5)
                    end_x2 = actual_center_x + 8 - (16 * stroke2_progress)
                    end_y2 = actual_center_y - 8 + (16 * stroke2_progress)
                    
                    self.canvas.create_line(
                        actual_center_x + 8, actual_center_y - 8,
                        end_x2, end_y2,
                        fill="white", width=5, capstyle="round"
                    )
        
        # Warning triangles around error
        if expand_progress > 0.6:
            self._draw_warning_indicators(actual_center_x, actual_center_y)
        
        # Modern error text with warning effect
        if expand_progress > 0.4:
            text_color = "#ff4444" if int(self.animation_frame / 8) % 2 else "#cc0000"
            
            # Text shadow
            self.canvas.create_text(
                actual_center_x + 1, center_y + 45,  # Use original center_y for text stability
                text="ERROR", font=("Segoe UI", 9, "bold"),
                fill="#440000"
            )
            # Main text
            self.canvas.create_text(
                actual_center_x, center_y + 44,
                text="ERROR", font=("Segoe UI", 9, "bold"),
                fill=text_color
            )
        
        # Auto-hide after 2.5 seconds
        if self.animation_frame > 50:  # ~2.5 seconds at 20 FPS
            if self.window:
                self.window.after(100, self.hide)
    
    def _draw_warning_indicators(self, center_x: int, center_y: int):
        """Draw warning triangle indicators around error"""
        triangle_count = 4
        for i in range(triangle_count):
            angle = i * (360 / triangle_count) + self.animation_frame * 3
            distance = 45
            
            x = center_x + distance * math.cos(math.radians(angle))
            y = center_y + distance * math.sin(math.radians(angle))
            
            # Warning triangle size with pulse
            triangle_size = 4 + int(2 * math.sin(self.animation_frame * 0.2 + i))
            
            # Draw warning triangle
            points = [
                x, y - triangle_size,          # Top point
                x - triangle_size, y + triangle_size,    # Bottom left
                x + triangle_size, y + triangle_size     # Bottom right
            ]
            
            self.canvas.create_polygon(
                points,
                fill="#ffaa00", outline="#ff6600", width=1
            )
            
            # Exclamation mark in triangle
            if triangle_size > 5:
                self.canvas.create_line(
                    x, y - 2, x, y + 1,
                    fill="white", width=1
                )
                self.canvas.create_oval(
                    x - 1, y + 2, x + 1, y + 4,
                    fill="white", outline=""
                )
    
    def _on_drag_start(self, event):
        """Start dragging the window"""
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # Change cursor to indicate dragging
        if self.canvas:
            self.canvas.configure(cursor="fleur")
        
        # Slight visual feedback when dragging starts
        if self.window:
            self.window.attributes("-alpha", min(1.0, self.window.attributes("-alpha") + 0.1))
    
    def _on_drag_motion(self, event):
        """Handle window dragging with smooth movement"""
        if self.window and self.dragging:
            # Calculate new position
            new_x = self.window.winfo_x() + (event.x - self.drag_start_x)
            new_y = self.window.winfo_y() + (event.y - self.drag_start_y)
            
            # Keep window within screen bounds
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            window_width = self.window.winfo_width()
            window_height = self.window.winfo_height()
            
            # Constrain to screen bounds
            new_x = max(0, min(new_x, screen_width - window_width))
            new_y = max(0, min(new_y, screen_height - window_height))
            
            # Apply new position
            self.window.geometry(f"+{new_x}+{new_y}")
    
    def _on_drag_end(self, event):
        """End dragging with smooth transition"""
        self.dragging = False
        
        # Restore cursor
        if self.canvas:
            self.canvas.configure(cursor="")
        
        # Restore transparency
        if self.window:
            self.window.attributes("-alpha", 0.85)
        
        # Optional: Snap to screen edges if close enough
        self._snap_to_edges()
    
    def _snap_to_edges(self):
        """Snap window to screen edges if close enough"""
        if not self.window:
            return
            
        try:
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            window_width = self.window.winfo_width()
            window_height = self.window.winfo_height()
            
            current_x = self.window.winfo_x()
            current_y = self.window.winfo_y()
            
            snap_distance = 30  # Pixels from edge to trigger snap
            new_x, new_y = current_x, current_y
            
            # Snap to left edge
            if current_x < snap_distance:
                new_x = 10
            # Snap to right edge  
            elif current_x > screen_width - window_width - snap_distance:
                new_x = screen_width - window_width - 10
            
            # Snap to top edge
            if current_y < snap_distance:
                new_y = 10
            # Snap to bottom edge
            elif current_y > screen_height - window_height - snap_distance:
                new_y = screen_height - window_height - 10
            
            # Apply snap if position changed
            if new_x != current_x or new_y != current_y:
                self.window.geometry(f"+{new_x}+{new_y}")
                
        except Exception as e:
            print(f"Snap to edges error: {e}")


class StatusDialogManager:
    """Manager for the status dialog with easy state transitions"""
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        self.parent_window = parent_window
        self.dialog: Optional[StatusDialog] = None
    
    def show_recording(self):
        """Show recording state"""
        print(f"DEBUG: StatusDialogManager.show_recording() called, parent_window={self.parent_window}")
        if not self.dialog:
            print("DEBUG: Creating new StatusDialog...")
            self.dialog = StatusDialog(self.parent_window)
        print("DEBUG: Calling dialog.show()...")
        self.dialog.show(DialogState.RECORDING)
    
    def show_processing(self):
        """Show processing state"""
        if self.dialog:
            self.dialog.set_state(DialogState.PROCESSING)
        else:
            self.dialog = StatusDialog(self.parent_window)
            self.dialog.show(DialogState.PROCESSING)
    
    def show_success(self):
        """Show success state (auto-hides)"""
        if self.dialog:
            self.dialog.set_state(DialogState.SUCCESS)
        else:
            self.dialog = StatusDialog(self.parent_window)
            self.dialog.show(DialogState.SUCCESS)
    
    def show_error(self):
        """Show error state (auto-hides)"""
        if self.dialog:
            self.dialog.set_state(DialogState.ERROR)
        else:
            self.dialog = StatusDialog(self.parent_window)
            self.dialog.show(DialogState.ERROR)
    
    def update_audio_level(self, level: float):
        """Update audio level visualization"""
        if self.dialog and self.dialog.current_state == DialogState.RECORDING:
            self.dialog.update_audio_level(level)
    
    def hide(self):
        """Hide the dialog"""
        if self.dialog:
            self.dialog.hide()
            self.dialog = None
    
    def is_visible(self) -> bool:
        """Check if dialog is currently visible"""
        return self.dialog is not None and self.dialog.is_visible


# Factory function for easy usage
def create_status_dialog_manager() -> StatusDialogManager:
    """Create a new status dialog manager"""
    return StatusDialogManager()

# Test function for debugging
def test_simple_dialog():
    """Test function to create a simple dialog for debugging"""
    print("DEBUG: Creating simple test dialog")
    
    # Create a simple window for testing
    test_window = ctk.CTkToplevel()
    test_window.title("Test Dialog")
    test_window.geometry("200x200+100+100")
    test_window.attributes("-topmost", True)
    
    # Add a simple label
    label = ctk.CTkLabel(test_window, text="TEST DIALOG\nShould be visible!")
    label.pack(expand=True)
    
    # Make sure it appears
    test_window.deiconify()
    test_window.lift()
    test_window.focus_force()
    
    print("DEBUG: Simple test dialog created")
    return test_window