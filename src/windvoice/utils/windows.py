"""
Windows-specific utilities for robust text field detection and UI automation
"""

import sys
import time
import ctypes
from ctypes import wintypes, windll, byref, sizeof, c_wchar_p, c_int, c_uint, c_void_p, c_long
from typing import Optional, Dict, Any, Tuple
from ..utils.logging import get_logger

# Windows API constants
GWL_STYLE = -16
IDC_IBEAM = 32513
IDC_ARROW = 32512
CBS_DROPDOWNLIST = 0x0003
EM_GETLINE = 0x00C4
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
WS_VISIBLE = 0x00000080

# Windows API structures
class POINT(ctypes.Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class CURSORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("hCursor", wintypes.HANDLE),
                ("ptScreenPos", POINT)]

class GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("hwndActive", wintypes.HWND),
                ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND),
                ("hwndMenuOwner", wintypes.HWND),
                ("hwndMoveSize", wintypes.HWND),
                ("hwndCaret", wintypes.HWND),
                ("rcCaret", wintypes.RECT)]

# Windows API availability check
if sys.platform == "win32":
    try:
        import win32gui
        import win32api
        import win32con
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
else:
    WIN32_AVAILABLE = False


class WindowsTextFieldDetector:
    """
    Robust Windows text field detection using native Windows APIs
    """
    
    def __init__(self):
        self.logger = get_logger("windows_detector")
        self.logger.info(f"Windows text field detector initialized - Win32: {WIN32_AVAILABLE}")
        
        # Cache for performance
        self._last_check_time = 0
        self._last_result = None
        self._cache_duration = 0.1  # 100ms cache
    
    def detect_active_text_field(self) -> bool:
        """
        Detect if active element is a text input field using robust Windows APIs
        
        Returns:
            bool: True if text field detected, False otherwise
        """
        if sys.platform != "win32":
            self.logger.warning("Not running on Windows - defaulting to False")
            return False
        
        # Use cache for performance (avoid excessive API calls)
        current_time = time.time()
        if (current_time - self._last_check_time) < self._cache_duration and self._last_result is not None:
            self.logger.debug(f"[DETECTION] Using cached result: {self._last_result}")
            return self._last_result
        
        self.logger.debug("[DETECTION] Starting Windows text field detection")
        result = False
        
        try:
            # Method 1: Win32 API control detection (most reliable)
            win32_result = self._detect_via_win32_enhanced()
            if win32_result is not None:
                result = win32_result
                self.logger.info(f"[DETECTION] Win32 API result: {result}")
            else:
                # Method 2: Cursor-based detection as fallback
                cursor_result = self._detect_via_cursor_enhanced()
                if cursor_result is not None:
                    result = cursor_result
                    self.logger.info(f"[DETECTION] Cursor detection result: {result}")
                else:
                    # Method 3: Behavioral test as last resort
                    result = self._detect_via_behavioral_test()
                    self.logger.info(f"[DETECTION] Behavioral test result: {result}")
        
        except Exception as e:
            self.logger.error(f"[DETECTION] Detection failed: {e}")
            result = False
        
        # Cache result
        self._last_check_time = current_time
        self._last_result = result
        
        return result
    
    def _detect_via_win32_enhanced(self) -> Optional[bool]:
        """
        Enhanced Win32 API detection with better error handling and control identification
        
        Returns:
            True: Text field detected
            False: Definitely not a text field
            None: Inconclusive
        """
        try:
            # Get foreground window
            foreground_hwnd = windll.user32.GetForegroundWindow()
            if not foreground_hwnd:
                self.logger.debug("[WIN32] No foreground window")
                return None
            
            # Get focused control using a more reliable method
            focused_hwnd = self._get_focused_control(foreground_hwnd)
            if not focused_hwnd:
                self.logger.debug("[WIN32] No focused control found")
                return None
            
            # Get control information
            class_name = self._get_window_class_name(focused_hwnd)
            if not class_name:
                self.logger.debug("[WIN32] Could not get class name")
                return None
            
            class_name = class_name.lower()
            self.logger.debug(f"[WIN32] Focused control class: {class_name}")
            
            # Check for text input control classes (comprehensive list)
            text_control_classes = {
                'edit',                       # Standard Edit controls
                'richedit',                   # RichEdit 1.0
                'richedit20a',                # RichEdit 2.0 ANSI
                'richedit20w',                # RichEdit 2.0 Unicode
                'richedit30w',                # RichEdit 3.0
                'richedit41w',                # RichEdit 4.1
                'richedit50w',                # RichEdit 5.0
                'msftedit_class',             # Modern RichEdit
                'richeditd2dpt',              # Direct2D RichEdit
                'consolewindowclass',         # Command prompt
                'scintilla',                  # Scintilla editor (Notepad++, VS Code)
                'internetexplorer_server',    # IE/Edge text areas
                'chrome_renderwidgethosthwnd', # Chrome text fields
                'mozilla_windowclass_1',      # Firefox text fields
                'textbox',                    # Generic text box
                'textboxviewhost',            # Modern text box host
                'textinputhost',              # Windows 10+ text input
            }
            
            # Direct match for known text controls
            if any(text_class in class_name for text_class in text_control_classes):
                self.logger.debug(f"[WIN32] Matched text control class: {class_name}")
                return True
            
            # Special handling for combo boxes
            if 'combobox' in class_name:
                return self._check_combobox_editability(focused_hwnd)
            
            # Check for known non-text controls
            non_text_classes = {
                'button',
                'static',
                'listbox',
                'scrollbar',
                'msctls_trackbar32',      # Slider
                'msctls_progress32',      # Progress bar
                'tooltips_class32',       # Tooltip
                'msctls_statusbar32',     # Status bar
                'syslistview32',          # List view
                'systreeview32',          # Tree view
                'systabcontrol32',        # Tab control
                'sysheader32',            # Header control
                'sysmonthcal32',          # Month calendar
                'sysdatetimepick32',      # Date/time picker (non-editable parts)
            }
            
            if any(non_text_class in class_name for non_text_class in non_text_classes):
                self.logger.debug(f"[WIN32] Matched non-text control class: {class_name}")
                return False
            
            # Additional check for modern app controls
            if self._is_modern_text_control(focused_hwnd):
                return True
            
            # Unknown class - inconclusive
            self.logger.debug(f"[WIN32] Unknown control class: {class_name}")
            return None
                
        except Exception as e:
            self.logger.debug(f"[WIN32] Enhanced detection failed: {e}")
            return None
    
    def _get_focused_control(self, foreground_hwnd: int) -> Optional[int]:
        """
        Get focused control handle using multiple methods for better reliability
        """
        try:
            # Method 1: Use GetGUIThreadInfo (most reliable for modern Windows)
            gui_thread_info = GUITHREADINFO()
            gui_thread_info.cbSize = sizeof(GUITHREADINFO)
            
            if windll.user32.GetGUIThreadInfo(0, byref(gui_thread_info)):
                if gui_thread_info.hwndFocus:
                    self.logger.debug(f"[WIN32] Found focused control via GetGUIThreadInfo: {gui_thread_info.hwndFocus}")
                    return gui_thread_info.hwndFocus
            
            # Method 2: Try GetFocus() with thread attachment
            current_thread = windll.kernel32.GetCurrentThreadId()
            foreground_thread = windll.user32.GetWindowThreadProcessId(foreground_hwnd, None)
            
            thread_attached = False
            if foreground_thread and foreground_thread != current_thread:
                result = windll.user32.AttachThreadInput(current_thread, foreground_thread, True)
                thread_attached = result != 0
            
            try:
                focused_hwnd = windll.user32.GetFocus()
                if focused_hwnd:
                    self.logger.debug(f"[WIN32] Found focused control via GetFocus: {focused_hwnd}")
                    return focused_hwnd
            finally:
                if thread_attached:
                    windll.user32.AttachThreadInput(current_thread, foreground_thread, False)
            
            # Method 3: Use foreground window as fallback
            self.logger.debug(f"[WIN32] Using foreground window as fallback: {foreground_hwnd}")
            return foreground_hwnd
            
        except Exception as e:
            self.logger.debug(f"[WIN32] Failed to get focused control: {e}")
            return foreground_hwnd  # Fallback to foreground window
    
    def _get_window_class_name(self, hwnd: int) -> Optional[str]:
        """
        Get window class name with better error handling
        """
        try:
            class_name_buffer = ctypes.create_unicode_buffer(256)
            length = windll.user32.GetClassNameW(hwnd, class_name_buffer, 256)
            
            if length > 0:
                return class_name_buffer.value
            return None
            
        except Exception as e:
            self.logger.debug(f"[WIN32] Failed to get class name: {e}")
            return None
    
    def _check_combobox_editability(self, hwnd: int) -> bool:
        """
        Check if a combo box has text input capability
        """
        try:
            style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            # If it's not a dropdown list only, it has text input
            is_editable = (style & CBS_DROPDOWNLIST) != CBS_DROPDOWNLIST
            self.logger.debug(f"[WIN32] ComboBox editability: {is_editable}")
            return is_editable
        except Exception as e:
            self.logger.debug(f"[WIN32] ComboBox style check failed: {e}")
            return False  # Assume non-editable if we can't determine
    
    def _is_modern_text_control(self, hwnd: int) -> bool:
        """
        Check for modern app text controls using additional heuristics
        """
        try:
            # Check if control accepts text input by testing message capability
            text_length = windll.user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0)
            
            # Valid response (>= 0) indicates text capability
            if text_length >= 0:
                # Additional check: verify control is visible and enabled
                style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
                if style & WS_VISIBLE:  # Control is visible
                    self.logger.debug("[WIN32] Modern text control detected via heuristics")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"[WIN32] Modern control check failed: {e}")
            return False
    
    def _detect_via_cursor_enhanced(self) -> Optional[bool]:
        """
        Enhanced cursor detection with better reliability
        
        Returns:
            True: I-beam cursor detected (likely text field)
            False: Non-text cursor detected
            None: Cannot determine cursor type
        """
        try:
            cursor_info = CURSORINFO()
            cursor_info.cbSize = sizeof(CURSORINFO)
            
            if not windll.user32.GetCursorInfo(byref(cursor_info)):
                self.logger.debug("[CURSOR] Failed to get cursor info")
                return None
            
            if cursor_info.flags == 0:  # Cursor hidden
                self.logger.debug("[CURSOR] Cursor is hidden")
                return None
            
            # Load standard cursors for comparison
            ibeam_cursor = windll.user32.LoadCursorW(None, IDC_IBEAM)
            arrow_cursor = windll.user32.LoadCursorW(None, IDC_ARROW)
            
            current_cursor = cursor_info.hCursor
            
            self.logger.debug(f"[CURSOR] Current: {current_cursor}, I-beam: {ibeam_cursor}")
            
            # Direct comparison with I-beam cursor
            if current_cursor == ibeam_cursor:
                self.logger.debug("[CURSOR] I-beam cursor detected")
                return True
            
            # If it's the standard arrow cursor, likely not a text field
            if current_cursor == arrow_cursor:
                self.logger.debug("[CURSOR] Arrow cursor detected")
                return False
            
            # Unknown cursor - inconclusive
            self.logger.debug(f"[CURSOR] Unknown cursor type: {current_cursor}")
            return None
                
        except Exception as e:
            self.logger.debug(f"[CURSOR] Enhanced cursor detection failed: {e}")
            return None
    
    def _detect_via_behavioral_test(self) -> bool:
        """
        Last resort: test if we can interact with the control like a text field
        This is a gentle test that shouldn't disrupt user experience much
        
        Returns:
            bool: True if control behaves like text field
        """
        try:
            self.logger.debug("[BEHAVIORAL] Starting gentle behavioral test")
            
            # Simple test: try to get text length using WM_GETTEXTLENGTH
            # This is safe and non-destructive
            foreground_hwnd = windll.user32.GetForegroundWindow()
            if not foreground_hwnd:
                return False
            
            focused_hwnd = self._get_focused_control(foreground_hwnd)
            if not focused_hwnd:
                return False
            
            # Test if control responds to text-related messages
            text_length = windll.user32.SendMessageW(focused_hwnd, WM_GETTEXTLENGTH, 0, 0)
            
            # A valid response (>= 0) suggests it's a text-capable control
            if text_length >= 0:
                self.logger.debug(f"[BEHAVIORAL] Control responded to WM_GETTEXTLENGTH with {text_length}")
                return True
            
            self.logger.debug("[BEHAVIORAL] Control did not respond to text messages")
            return False
            
        except Exception as e:
            self.logger.debug(f"[BEHAVIORAL] Behavioral test failed: {e}")
            return False
    
    def get_focused_window_info(self) -> Dict[str, Any]:
        """
        Get information about the currently focused window for debugging
        
        Returns:
            dict: Information about focused window and control
        """
        info = {
            'platform': sys.platform,
            'win32_available': WIN32_AVAILABLE,
            'foreground_window': None,
            'focused_control': None,
            'control_class': None,
            'window_title': None,
            'detection_result': None,
            'cursor_type': None
        }
        
        if sys.platform != "win32":
            return info
        
        try:
            # Get foreground window
            foreground_hwnd = windll.user32.GetForegroundWindow()
            if foreground_hwnd:
                info['foreground_window'] = foreground_hwnd
                
                # Get window title
                try:
                    title_buffer = ctypes.create_unicode_buffer(512)
                    length = windll.user32.GetWindowTextW(foreground_hwnd, title_buffer, 512)
                    if length > 0:
                        info['window_title'] = title_buffer.value
                except Exception:
                    pass
                
                # Get focused control
                focused_hwnd = self._get_focused_control(foreground_hwnd)
                if focused_hwnd:
                    info['focused_control'] = focused_hwnd
                    info['control_class'] = self._get_window_class_name(focused_hwnd)
            
            # Run detection
            info['detection_result'] = self.detect_active_text_field()
            
            # Get cursor info
            try:
                cursor_info = CURSORINFO()
                cursor_info.cbSize = sizeof(CURSORINFO)
                if windll.user32.GetCursorInfo(byref(cursor_info)):
                    info['cursor_handle'] = cursor_info.hCursor
                    
                    # Check if it's I-beam
                    ibeam_cursor = windll.user32.LoadCursorW(None, IDC_IBEAM)
                    info['is_ibeam_cursor'] = cursor_info.hCursor == ibeam_cursor
            except Exception:
                pass
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def clear_cache(self):
        """Clear detection cache - useful for testing or when focus changes"""
        self._last_check_time = 0
        self._last_result = None
        self.logger.debug("Detection cache cleared")