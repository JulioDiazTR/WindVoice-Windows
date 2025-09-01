import asyncio
from typing import Callable, Optional
from pynput import keyboard
import threading
from ..core.exceptions import HotkeyError


class HotkeyManager:
    def __init__(self):
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self.hotkey_string: str = "ctrl+shift+space"
        self.on_hotkey: Optional[Callable] = None
        self._loop = None
        
    def set_hotkey_callback(self, callback: Callable):
        self.on_hotkey = callback
        
    def set_hotkey(self, hotkey_string: str):
        self.hotkey_string = hotkey_string
        
    def _parse_hotkey(self, hotkey_string: str) -> str:
        parts = hotkey_string.lower().split('+')
        parsed_parts = []
        
        for part in parts:
            part = part.strip()
            if part == 'ctrl':
                parsed_parts.append('<ctrl>')
            elif part == 'shift':
                parsed_parts.append('<shift>')
            elif part == 'alt':
                parsed_parts.append('<alt>')
            elif part == 'space':
                parsed_parts.append('<space>')
            elif part == 'enter':
                parsed_parts.append('<enter>')
            elif part == 'tab':
                parsed_parts.append('<tab>')
            elif len(part) == 1:
                parsed_parts.append(part)
            else:
                parsed_parts.append(f'<{part}>')
                
        return '+'.join(parsed_parts)
        
    def _on_hotkey_pressed(self):
        if self.on_hotkey:
            if asyncio.iscoroutinefunction(self.on_hotkey):
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.on_hotkey(), self._loop)
                else:
                    try:
                        asyncio.create_task(self.on_hotkey())
                    except RuntimeError:
                        pass
            else:
                self.on_hotkey()
    
    def start(self, event_loop=None):
        if self.listener:
            self.stop()
            
        self._loop = event_loop
        
        try:
            parsed_hotkey = self._parse_hotkey(self.hotkey_string)
            hotkeys = {parsed_hotkey: self._on_hotkey_pressed}
            
            self.listener = keyboard.GlobalHotKeys(hotkeys)
            self.listener.start()
            
        except Exception as e:
            raise HotkeyError(f"Failed to register hotkey '{self.hotkey_string}': {e}")
    
    def stop(self):
        if self.listener:
            try:
                self.listener.stop()
                self.listener = None
            except Exception as e:
                print(f"Warning: Error stopping hotkey listener: {e}")
    
    def is_running(self) -> bool:
        return self.listener is not None and self.listener.running
    
    def test_hotkey(self, hotkey_string: str) -> bool:
        try:
            parsed = self._parse_hotkey(hotkey_string)
            test_listener = keyboard.GlobalHotKeys({parsed: lambda: None})
            test_listener.start()
            test_listener.stop()
            return True
        except Exception:
            return False