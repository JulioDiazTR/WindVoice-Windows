import time
from pynput import keyboard
from pynput.keyboard import Key
import pyperclip
from typing import Optional
from ..core.exceptions import TextInjectionError


class TextInjectionService:
    def __init__(self):
        self.keyboard_controller = keyboard.Controller()
        
    def inject_text_direct(self, text: str) -> bool:
        try:
            # Direct typing method
            for char in text:
                self.keyboard_controller.press(char)
                self.keyboard_controller.release(char)
                time.sleep(0.001)  # Small delay between characters
            
            return True
            
        except Exception as e:
            print(f"Direct typing failed: {e}")
            return False
    
    def inject_text_clipboard(self, text: str) -> bool:
        try:
            # Save current clipboard content
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                original_clipboard = ""
            
            # Set text to clipboard
            pyperclip.copy(text)
            time.sleep(0.05)  # Small delay to ensure clipboard is set
            
            # Paste using Ctrl+V
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('v')
            self.keyboard_controller.release('v')
            self.keyboard_controller.release(Key.ctrl)
            
            time.sleep(0.1)  # Wait for paste to complete
            
            # Restore original clipboard (optional, can be disabled for performance)
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            print(f"Clipboard injection failed: {e}")
            return False
    
    def inject_text(self, text: str, method: str = "auto") -> bool:
        if not text or not text.strip():
            raise TextInjectionError("Cannot inject empty text")
        
        text = text.strip()
        
        try:
            if method == "direct":
                return self.inject_text_direct(text)
            elif method == "clipboard":
                return self.inject_text_clipboard(text)
            elif method == "auto":
                # Try clipboard first (more reliable for large text)
                if len(text) > 100:
                    if self.inject_text_clipboard(text):
                        return True
                    return self.inject_text_direct(text)
                else:
                    # For short text, try direct first
                    if self.inject_text_direct(text):
                        return True
                    return self.inject_text_clipboard(text)
            else:
                raise TextInjectionError(f"Unknown injection method: {method}")
                
        except Exception as e:
            raise TextInjectionError(f"Text injection failed: {e}")
    
    def detect_active_text_field(self) -> bool:
        try:
            # Simple detection: try to select all text and see if anything happens
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass
            
            # Try Ctrl+A to select all
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('a')
            self.keyboard_controller.release('a')
            self.keyboard_controller.release(Key.ctrl)
            
            time.sleep(0.05)
            
            # Try Ctrl+C to copy
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('c')
            self.keyboard_controller.release('c')
            self.keyboard_controller.release(Key.ctrl)
            
            time.sleep(0.05)
            
            # Check if clipboard changed
            try:
                new_clipboard = pyperclip.paste()
                has_text_field = new_clipboard != original_clipboard
                
                # Restore original clipboard
                pyperclip.copy(original_clipboard)
                
                return has_text_field
            except:
                return False
                
        except Exception:
            return False
    
    def send_key_combination(self, *keys):
        try:
            # Press all keys
            for key in keys:
                if isinstance(key, str):
                    self.keyboard_controller.press(key)
                else:
                    self.keyboard_controller.press(key)
            
            # Release all keys in reverse order
            for key in reversed(keys):
                if isinstance(key, str):
                    self.keyboard_controller.release(key)
                else:
                    self.keyboard_controller.release(key)
                    
        except Exception as e:
            raise TextInjectionError(f"Failed to send key combination: {e}")
    
    def clear_current_selection(self):
        try:
            # Send Delete key to clear current selection
            self.keyboard_controller.press(Key.delete)
            self.keyboard_controller.release(Key.delete)
        except Exception as e:
            print(f"Warning: Failed to clear selection: {e}")
    
    def test_injection(self) -> bool:
        try:
            test_text = "WindVoice Test"
            return self.inject_text(test_text, method="clipboard")
        except Exception:
            return False