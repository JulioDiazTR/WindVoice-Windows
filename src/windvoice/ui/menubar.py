import pystray
from PIL import Image, ImageDraw
from typing import Callable, Optional
import threading
import asyncio
from ..core.exceptions import WindVoiceError


class SystemTrayService:
    def __init__(self, on_settings: Optional[Callable] = None, on_quit: Optional[Callable] = None):
        self.on_settings = on_settings
        self.on_quit = on_quit
        self.icon: Optional[pystray.Icon] = None
        self.recording = False
        self._loop = None
        
    def create_icon_image(self, recording: bool = False) -> Image.Image:
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        
        if recording:
            draw.ellipse([8, 8, width-8, height-8], fill=(255, 0, 0, 255), outline=(255, 255, 255, 255), width=2)
            draw.ellipse([20, 20, width-20, height-20], fill=(255, 255, 255, 255))
        else:
            draw.ellipse([8, 8, width-8, height-8], fill=(0, 120, 255, 255), outline=(255, 255, 255, 255), width=2)
            inner_points = []
            for angle in range(0, 360, 120):
                import math
                x = 32 + 15 * math.cos(math.radians(angle - 90))
                y = 32 + 15 * math.sin(math.radians(angle - 90))
                inner_points.append((x, y))
            draw.polygon(inner_points, fill=(255, 255, 255, 255))
            
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

    def set_recording_state(self, recording: bool):
        if self.recording != recording:
            self.recording = recording
            if self.icon:
                self.icon.icon = self.create_icon_image(recording)
                self.icon.menu = self._setup_menu()

    def show_notification(self, title: str, message: str):
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                print(f"{title}: {message}")

    def is_running(self) -> bool:
        return self.icon is not None and hasattr(self, 'tray_thread') and self.tray_thread.is_alive()