import pystray
from PIL import Image, ImageDraw
from typing import Callable, Optional
import threading
import asyncio
import time
from ..core.exceptions import WindVoiceError
from ..utils.logging import get_logger


class SystemTrayService:
    def __init__(self, on_settings: Optional[Callable] = None, on_quit: Optional[Callable] = None):
        self.logger = get_logger("system_tray")
        self.on_settings = on_settings
        self.on_quit = on_quit
        self.icon: Optional[pystray.Icon] = None
        self.recording = False
        self._loop = None
        
        # Visual feedback for recording
        self.animation_timer: Optional[threading.Timer] = None
        self.animation_frame = 0
        self.recording_level = 0.0
        
    def create_icon_image(self, recording: bool = False, level: float = 0.0) -> Image.Image:
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        
        if recording:
            # Animated recording indicator with level visualization
            import math
            
            # Pulsing red circle based on recording level
            pulse_intensity = int(128 + 127 * math.sin(self.animation_frame * 0.3))
            level_intensity = min(255, int(100 + level * 500))  # Scale level to visual intensity
            
            # Outer ring shows level
            ring_color = (level_intensity, 0, 0, 255)
            draw.ellipse([4, 4, width-4, height-4], outline=ring_color, width=4)
            
            # Inner circle pulses
            inner_color = (255, pulse_intensity//2, pulse_intensity//2, 255)
            draw.ellipse([12, 12, width-12, height-12], fill=inner_color)
            
            # Microphone icon
            mic_width = 8
            mic_height = 12
            mic_x = 32 - mic_width//2
            mic_y = 32 - mic_height//2
            
            # Mic body
            draw.rectangle([mic_x, mic_y, mic_x + mic_width, mic_y + mic_height], 
                         fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
            
            # Mic base
            draw.rectangle([mic_x - 2, mic_y + mic_height, mic_x + mic_width + 2, mic_y + mic_height + 3], 
                         fill=(255, 255, 255, 255))
            
            # Level bars around microphone
            if level > 0.05:
                bar_count = min(5, int(level * 10))
                for i in range(bar_count):
                    angle = i * (360 / 8)
                    radius = 25 + i * 2
                    x = 32 + radius * math.cos(math.radians(angle))
                    y = 32 + radius * math.sin(math.radians(angle))
                    bar_height = 3 + i
                    draw.ellipse([x-1, y-bar_height//2, x+1, y+bar_height//2], 
                               fill=(255, 255, 255, 200))
                               
        else:
            # Normal WindVoice icon
            draw.ellipse([8, 8, width-8, height-8], fill=(0, 120, 255, 255), outline=(255, 255, 255, 255), width=2)
            
            # WindVoice icon - stylized "W" or microphone
            inner_points = []
            for angle in range(0, 360, 120):
                import math
                x = 32 + 15 * math.cos(math.radians(angle - 90))
                y = 32 + 15 * math.sin(math.radians(angle - 90))
                inner_points.append((x, y))
            draw.polygon(inner_points, fill=(255, 255, 255, 255))
            
        self.animation_frame += 1
        return image

    def _setup_menu(self):
        return pystray.Menu(
            pystray.MenuItem("WindVoice", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Status: Ready" if not self.recording else "Status: Recording",
                lambda: None, 
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._on_settings_click),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit_click)
        )

    def _on_settings_click(self, icon, item):
        if self.on_settings:
            if asyncio.iscoroutinefunction(self.on_settings):
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.on_settings(), self._loop)
                else:
                    asyncio.create_task(self.on_settings())
            else:
                self.on_settings()

    def _on_quit_click(self, icon, item):
        if self.on_quit:
            if asyncio.iscoroutinefunction(self.on_quit):
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.on_quit(), self._loop)
                else:
                    asyncio.create_task(self.on_quit())
            else:
                self.on_quit()
        self.stop()

    def start(self, event_loop=None):
        self._loop = event_loop
        self.icon = pystray.Icon(
            "WindVoice",
            self.create_icon_image(),
            "WindVoice - Voice Dictation",
            menu=self._setup_menu()
        )
        
        def run_icon():
            try:
                self.icon.run()
            except Exception as e:
                print(f"System tray error: {e}")
        
        self.tray_thread = threading.Thread(target=run_icon, daemon=True)
        self.tray_thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()

    def set_recording_state(self, recording: bool, level: float = 0.0):
        """Set recording state with optional level for visual feedback"""
        if self.recording != recording:
            self.recording = recording
            self.recording_level = level
            
            if recording:
                # Start animation timer for recording feedback
                self._start_recording_animation()
            else:
                # Stop animation timer
                self._stop_recording_animation()
                
            if self.icon:
                self.icon.icon = self.create_icon_image(recording, level)
                self.icon.menu = self._setup_menu()
                
    def update_recording_level(self, level: float):
        """Update recording level for visual feedback"""
        if self.recording:
            self.recording_level = level
            if self.icon:
                try:
                    self.icon.icon = self.create_icon_image(True, level)
                except OSError as e:
                    # Handle Windows icon handle errors gracefully
                    print(f"Warning: Icon update failed: {e}")
                
    def _start_recording_animation(self):
        """Start animated recording feedback"""
        def update_animation():
            if self.recording and self.icon:
                try:
                    self.icon.icon = self.create_icon_image(True, self.recording_level)
                except OSError as e:
                    # Handle Windows icon handle errors gracefully
                    print(f"Warning: Icon update failed: {e}")
                
                # Schedule next frame
                self.animation_timer = threading.Timer(0.1, update_animation)
                self.animation_timer.start()
                
        # Start the animation loop
        if self.animation_timer:
            self.animation_timer.cancel()
        update_animation()
        
    def _stop_recording_animation(self):
        """Stop recording animation"""
        if self.animation_timer:
            self.animation_timer.cancel()
            self.animation_timer = None

    def show_notification(self, title: str, message: str):
        self.logger.info(f"[TRAY] show_notification called: '{title}' - '{message}'")
        if self.icon:
            try:
                self.logger.info(f"[TRAY] Calling icon.notify with message='{message}', title='{title}'")
                self.icon.notify(message, title)
                self.logger.info(f"[TRAY] icon.notify completed successfully")
            except Exception as e:
                self.logger.error(f"[TRAY] icon.notify failed: {e}")
                print(f"{title}: {message}")
        else:
            self.logger.error(f"[TRAY] No system tray icon available!")
            print(f"{title}: {message}")

    def is_running(self) -> bool:
        return self.icon is not None and hasattr(self, 'tray_thread') and self.tray_thread.is_alive()