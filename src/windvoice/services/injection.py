import time
from pynput import keyboard
from pynput.keyboard import Key
import pyperclip
from typing import Optional
from ..core.exceptions import TextInjectionError
from ..utils.logging import get_logger


class TextInjectionService:
    def __init__(self):
        self.logger = get_logger("injection")
        self.keyboard_controller = keyboard.Controller()
        
    def inject_text_direct(self, text: str) -> bool:
        """Inject text by typing each character directly - improved method"""
        try:
            self.logger.debug(f"[DIRECT] Starting direct text injection for {len(text)} characters")
            
            # Give focus time to settle
            time.sleep(0.05)
            
            # Process text in chunks for better performance with long text
            chunk_size = 50  # Process 50 characters at a time
            total_chunks = (len(text) + chunk_size - 1) // chunk_size
            
            for chunk_idx in range(0, len(text), chunk_size):
                chunk = text[chunk_idx:chunk_idx + chunk_size]
                current_chunk_num = (chunk_idx // chunk_size) + 1
                
                self.logger.debug(f"[DIRECT] Processing chunk {current_chunk_num}/{total_chunks}: '{chunk[:20]}{'...' if len(chunk) > 20 else ''}'")
                
                for i, char in enumerate(chunk):
                    try:
                        # Handle special characters
                        if char == '\n':
                            # Press Enter for newlines
                            self.keyboard_controller.press(Key.enter)
                            self.keyboard_controller.release(Key.enter)
                            time.sleep(0.01)
                        elif char == '\t':
                            # Press Tab for tabs
                            self.keyboard_controller.press(Key.tab)
                            self.keyboard_controller.release(Key.tab)
                            time.sleep(0.01)
                        else:
                            # Regular character
                            self.keyboard_controller.press(char)
                            self.keyboard_controller.release(char)
                            time.sleep(0.002)  # Slightly longer delay for reliability
                            
                    except Exception as char_e:
                        self.logger.warning(f"[DIRECT] Failed to type character '{char}' at position {chunk_idx + i}: {char_e}")
                        # For problematic characters, try to continue
                        continue
                
                # Small pause between chunks
                if current_chunk_num < total_chunks:
                    time.sleep(0.01)
            
            self.logger.info(f"[DIRECT] Direct text injection completed successfully for {len(text)} characters")
            return True
            
        except Exception as e:
            self.logger.error(f"[DIRECT] Direct typing failed: {e}")
            return False
    
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
            time.sleep(0.08)  # Slightly longer delay to ensure clipboard is set
            
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
            
            time.sleep(0.15)  # Wait for paste to complete
            
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
    
    def inject_text_with_focus_preservation(self, text: str) -> bool:
        """
        Alternative injection method that tries to preserve focus and cursor position.
        Uses a combination of techniques to be less disruptive than clipboard.
        """
        try:
            self.logger.debug(f"[FOCUS_PRESERVE] Starting focus-preserving injection for {len(text)} characters")
            
            # Small delay to ensure focus is stable
            time.sleep(0.03)
            
            # For very short text (under 10 chars), type directly
            if len(text) <= 10:
                return self.inject_text_direct(text)
            
            # For longer text, try a hybrid approach
            # Split into smaller chunks and type each chunk directly
            words = text.split(' ')
            
            for i, word in enumerate(words):
                # Type the word directly
                for char in word:
                    try:
                        self.keyboard_controller.press(char)
                        self.keyboard_controller.release(char)
                        time.sleep(0.003)  # Slightly slower for reliability
                    except Exception:
                        continue
                
                # Add space between words (except for last word)
                if i < len(words) - 1:
                    self.keyboard_controller.press(' ')
                    self.keyboard_controller.release(' ')
                    time.sleep(0.005)
                
                # Small pause every few words to prevent overwhelming the system
                if i > 0 and i % 10 == 0:
                    time.sleep(0.01)
            
            self.logger.info(f"[FOCUS_PRESERVE] Focus-preserving injection completed for {len(text)} characters")
            return True
            
        except Exception as e:
            self.logger.error(f"[FOCUS_PRESERVE] Focus-preserving injection failed: {e}")
            return False
    
    def inject_text(self, text: str, method: str = "auto") -> bool:
        if not text or not text.strip():
            raise TextInjectionError("Cannot inject empty text")
        
        text = text.strip()
        self.logger.info(f"[INJECTION] Starting text injection - method: {method}, text length: {len(text)}, text preview: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # First check if there's an active text field
        has_active_field = self.detect_active_text_field()
        self.logger.info(f"[INJECTION] Active text field detected: {has_active_field}")
        
        if not has_active_field:
            self.logger.warning("[INJECTION] No active text field detected - aborting injection to prevent unwanted typing")
            return False
        
        try:
            success = False
            if method == "direct":
                success = self.inject_text_direct(text)
            elif method == "clipboard":
                success = self.inject_text_clipboard(text)
            elif method == "auto":
                # Multi-tier approach to avoid clipboard usage
                self.logger.debug("[INJECTION] Using direct method first (preserving user clipboard)")
                success = self.inject_text_direct(text)
                
                if not success:
                    self.logger.info("[INJECTION] Direct method failed, trying focus-preserving method")
                    success = self.inject_text_with_focus_preservation(text)
                    
                    if not success:
                        self.logger.warning("[INJECTION] All clipboard-free methods failed, using clipboard as LAST RESORT")
                        success = self.inject_text_clipboard(text)
            else:
                raise TextInjectionError(f"Unknown injection method: {method}")
            
            self.logger.info(f"[INJECTION] Text injection result: {success}")
            return success
                
        except Exception as e:
            self.logger.error(f"[INJECTION] Text injection failed with exception: {e}")
            raise TextInjectionError(f"Text injection failed: {e}")
    
    def detect_active_text_field(self) -> bool:
        """
        Detect if there's an active text field by trying to interact with it.
        This is a heuristic approach that may have false positives/negatives.
        """
        try:
            self.logger.debug("[DETECTION] Starting active text field detection")
            
            # Save current clipboard content
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
                self.logger.debug(f"[DETECTION] Original clipboard length: {len(original_clipboard) if original_clipboard else 0}")
            except Exception as e:
                self.logger.debug(f"[DETECTION] Failed to get original clipboard: {e}")
                original_clipboard = ""
            
            # Give focus a moment to settle
            time.sleep(0.02)
            
            # Try Ctrl+A to select all text in current field
            self.logger.debug("[DETECTION] Sending Ctrl+A")
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('a')
            self.keyboard_controller.release('a')
            self.keyboard_controller.release(Key.ctrl)
            
            time.sleep(0.08)  # Longer wait for selection
            
            # Try Ctrl+C to copy selected text
            self.logger.debug("[DETECTION] Sending Ctrl+C")
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('c')
            self.keyboard_controller.release('c')
            self.keyboard_controller.release(Key.ctrl)
            
            time.sleep(0.08)  # Longer wait for copy operation
            
            # Check if clipboard changed (indicating text was selected and copied)
            try:
                new_clipboard = pyperclip.paste()
                
                self.logger.debug(f"[DETECTION] New clipboard length: {len(new_clipboard) if new_clipboard else 0}")
                
                # More conservative detection: only return True if clipboard actually changed
                # AND the new content is different from original (not just empty vs empty)
                clipboard_changed = new_clipboard != original_clipboard
                has_meaningful_selection = (
                    clipboard_changed and 
                    new_clipboard is not None and 
                    len(new_clipboard.strip()) > 0 and 
                    new_clipboard.strip() != original_clipboard.strip()
                )
                
                self.logger.debug(f"[DETECTION] Clipboard changed: {clipboard_changed}")
                self.logger.debug(f"[DETECTION] Has meaningful selection: {has_meaningful_selection}")
                
                # Restore original clipboard to avoid disrupting user's workflow
                try:
                    pyperclip.copy(original_clipboard)
                except Exception as e:
                    self.logger.debug(f"[DETECTION] Failed to restore clipboard: {e}")
                
                # Conservative approach: only detect active field if we actually selected something meaningful
                has_text_field = has_meaningful_selection
                
                self.logger.info(f"[DETECTION] Active text field detected: {has_text_field}")
                return has_text_field
                
            except Exception as e:
                self.logger.debug(f"[DETECTION] Clipboard check failed: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"[DETECTION] Text field detection failed: {e}")
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