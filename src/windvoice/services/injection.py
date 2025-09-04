import time
from pynput import keyboard
from pynput.keyboard import Key
import pyperclip
from typing import Optional
from ..core.exceptions import TextInjectionError
from ..utils.logging import get_logger
from ..utils.windows import WindowsTextFieldDetector


class TextInjectionService:
    def __init__(self):
        self.logger = get_logger("injection")
        self.keyboard_controller = keyboard.Controller()
        self.text_field_detector = WindowsTextFieldDetector()
        
    def inject_text_direct(self, text: str) -> bool:
        """Inject text by typing each character directly - optimized for speed"""
        try:
            self.logger.debug(f"[DIRECT] Starting direct text injection for {len(text)} characters")
            
            # PERFORMANCE: No delay needed - Windows handles focus automatically
            
            # Type the text with optimized timing
            failed_chars = 0
            for i, char in enumerate(text):
                try:
                    # Handle special characters
                    if char == '\n':
                        # Press Enter for newlines
                        self.keyboard_controller.press(Key.enter)
                        self.keyboard_controller.release(Key.enter)
                        # No delay for newlines - let system handle it
                    elif char == '\t':
                        # Press Tab for tabs
                        self.keyboard_controller.press(Key.tab)
                        self.keyboard_controller.release(Key.tab)
                    else:
                        # Regular character - no delay between characters for speed
                        self.keyboard_controller.press(char)
                        self.keyboard_controller.release(char)
                        
                except Exception as char_e:
                    self.logger.debug(f"[DIRECT] Failed to type character '{char}' at position {i}: {char_e}")
                    failed_chars += 1
                    # More lenient threshold for performance
                    if failed_chars > len(text) * 0.1:  # Allow 10% failure rate
                        self.logger.error(f"[DIRECT] Too many character failures ({failed_chars})")
                        return False
            
            # Success is based on reasonable failure rate
            success_rate = (len(text) - failed_chars) / len(text)
            success = success_rate >= 0.9  # 90% success rate
            
            self.logger.info(f"[DIRECT] Direct injection completed - success rate: {success_rate:.2%}")
            return success
            
        except Exception as e:
            self.logger.error(f"[DIRECT] Direct typing failed: {e}")
            return False
    
    # Simplified approach - let typing success/failure be the indicator
    
    def inject_text_clipboard(self, text: str) -> bool:
        """
        Inject text by copying to clipboard and pasting.
        WARNING: This temporarily modifies the user's clipboard!
        Only used as last resort when direct injection fails.
        """
        try:
            self.logger.warning(f"[CLIPBOARD] Using clipboard method as LAST RESORT for {len(text)} characters - user clipboard will be temporarily affected")
            
            # Save current clipboard content - critical for user experience
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
                self.logger.info(f"[CLIPBOARD] Saved original clipboard: {len(original_clipboard) if original_clipboard else 0} chars")
            except Exception as e:
                self.logger.error(f"[CLIPBOARD] CRITICAL: Failed to get original clipboard: {e}")
                # Continue anyway, but warn user
                original_clipboard = ""
            
            # Set text to clipboard
            self.logger.debug("[CLIPBOARD] Copying text to clipboard")
            pyperclip.copy(text)
            time.sleep(0.02)  # PERFORMANCE: Minimal delay for clipboard synchronization
            
            # Verify clipboard was set
            try:
                clipboard_check = pyperclip.paste()
                if clipboard_check != text:
                    self.logger.warning(f"[CLIPBOARD] Clipboard verification failed - expected {len(text)} chars, got {len(clipboard_check) if clipboard_check else 0}")
            except Exception as e:
                self.logger.debug(f"[CLIPBOARD] Clipboard verification failed: {e}")
            
            # Paste using Ctrl+V
            self.logger.debug("[CLIPBOARD] Sending Ctrl+V")
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('v')
            self.keyboard_controller.release('v')
            self.keyboard_controller.release(Key.ctrl)
            
            time.sleep(0.05)  # PERFORMANCE: Reduced wait for paste completion
            
            # CRITICAL: Restore original clipboard immediately to minimize disruption
            try:
                pyperclip.copy(original_clipboard)
                self.logger.info("[CLIPBOARD] Successfully restored original clipboard content")
            except Exception as e:
                self.logger.error(f"[CLIPBOARD] CRITICAL: Failed to restore original clipboard: {e}")
                # This is bad for user experience but not fatal
            
            self.logger.warning("[CLIPBOARD] Clipboard text injection completed - clipboard restoration attempted")
            return True
            
        except Exception as e:
            self.logger.error(f"[CLIPBOARD] Clipboard injection failed: {e}")
            return False
    
    # Removed inject_text_with_focus_preservation to simplify and avoid clipboard usage
    
    def inject_text(self, text: str, method: str = "auto") -> bool:
        if not text or not text.strip():
            raise TextInjectionError("Cannot inject empty text")
        
        text = text.strip()
        self.logger.info(f"[INJECTION] Starting text injection - method: {method}, length: {len(text)}")
        
        # Clear cache to ensure fresh detection
        self.text_field_detector.clear_cache()
        
        # Use enhanced Windows API-based text field detection
        start_time = time.time()
        has_text_field = self.text_field_detector.detect_active_text_field()
        detection_time = time.time() - start_time
        
        self.logger.info(f"[INJECTION] Text field detected: {has_text_field} (took {detection_time:.3f}s)")
        
        if not has_text_field:
            self.logger.info("[INJECTION] No text field detected - returning False for dialog fallback")
            return False
        
        # Text field detected - proceed with optimized injection
        try:
            success = False
            injection_start = time.time()
            
            if method == "auto":
                # Optimized strategy based on text length
                if len(text) <= 200:  # Increased threshold for direct typing
                    self.logger.debug("[INJECTION] Using direct typing for short text")
                    success = self.inject_text_direct(text)
                    
                    # Quick fallback to clipboard if direct fails
                    if not success:
                        self.logger.debug("[INJECTION] Direct failed, trying clipboard")
                        success = self.inject_text_clipboard_safe(text)
                else:
                    # For longer text, clipboard is more reliable
                    self.logger.debug("[INJECTION] Using clipboard for long text")
                    success = self.inject_text_clipboard_safe(text)
                    
            elif method == "clipboard":
                success = self.inject_text_clipboard_safe(text)
            elif method == "direct":
                success = self.inject_text_direct(text)
            else:
                raise TextInjectionError(f"Unknown injection method: {method}")
            
            injection_time = time.time() - injection_start
            
            if success:
                self.logger.info(f"[INJECTION] Text injection completed successfully (took {injection_time:.3f}s)")
                return True
            else:
                self.logger.warning(f"[INJECTION] All injection methods failed (took {injection_time:.3f}s) - returning False for dialog fallback")
                return False
                
        except Exception as e:
            self.logger.error(f"[INJECTION] Text injection failed with exception: {e}")
            return False
    
    def get_focused_window_debug_info(self) -> dict:
        """
        Get debug information about the currently focused window for troubleshooting
        """
        try:
            return self.text_field_detector.get_focused_window_info()
        except Exception as e:
            self.logger.error(f"Failed to get focused window info: {e}")
            return {"error": str(e)}
    
    def detect_text_field_fallback(self) -> bool:
        """
        DEPRECATED: Legacy fallback detection method
        Use Windows API detection instead for better performance and reliability
        """
        self.logger.warning("[FALLBACK] Using deprecated fallback detection - consider upgrading")
        
        # Delegate to the new Windows API detector for consistency
        return self.text_field_detector.detect_active_text_field()
    
    def inject_text_clipboard_safe(self, text: str) -> bool:
        """
        Optimized clipboard-based injection with guaranteed restoration
        """
        original_clipboard = None
        
        try:
            self.logger.debug(f"[CLIPBOARD_SAFE] Starting clipboard injection for {len(text)} chars")
            
            # Step 1: Save original clipboard (quick backup)
            try:
                original_clipboard = pyperclip.paste()
            except Exception as e:
                self.logger.debug(f"[CLIPBOARD_SAFE] Could not backup clipboard: {e}")
                original_clipboard = ""
            
            # Step 2: Copy our text to clipboard
            pyperclip.copy(text)
            time.sleep(0.01)  # PERFORMANCE: Minimal clipboard sync delay
            
            # Step 3: Quick verification (single attempt for speed)
            try:
                verify_clipboard = pyperclip.paste()
                if verify_clipboard != text:
                    self.logger.warning("[CLIPBOARD_SAFE] Clipboard verification failed - proceeding anyway")
            except Exception:
                pass  # Continue anyway for performance
            
            # Step 4: Paste (Ctrl+V) - optimized timing
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('v')
            self.keyboard_controller.release('v')
            self.keyboard_controller.release(Key.ctrl)
            
            time.sleep(0.02)  # PERFORMANCE: Minimal wait for paste operation
            
            self.logger.debug("[CLIPBOARD_SAFE] Clipboard injection completed")
            return True
            
        except Exception as e:
            self.logger.error(f"[CLIPBOARD_SAFE] Clipboard injection failed: {e}")
            return False
            
        finally:
            # CRITICAL: Always restore original clipboard
            if original_clipboard is not None:
                try:
                    pyperclip.copy(original_clipboard)
                    self.logger.debug("[CLIPBOARD_SAFE] Original clipboard restored")
                except Exception as e:
                    self.logger.error(f"[CLIPBOARD_SAFE] Failed to restore clipboard: {e}")
    
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