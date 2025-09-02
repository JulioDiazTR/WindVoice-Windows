#!/usr/bin/env python3
"""
Test script for Windows text field detection
Run this script and then click on different applications to test text field detection
"""

import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from windvoice.utils.windows import WindowsTextFieldDetector
from windvoice.utils.logging import get_logger

def main():
    print("Windows Text Field Detection Test")
    print("=" * 40)
    print("Instructions:")
    print("1. Run this script")
    print("2. Click on different windows/controls")
    print("3. See the detection results in real-time")
    print("4. Press Ctrl+C to exit")
    print()
    
    detector = WindowsTextFieldDetector()
    logger = get_logger("test")
    
    last_result = None
    last_window = None
    
    try:
        while True:
            # Test detection
            result = detector.detect_active_text_field()
            
            # Get detailed info
            info = detector.get_focused_window_info()
            
            current_window = info.get('window_title', 'Unknown')
            control_class = info.get('control_class', 'Unknown')
            
            # Only print if something changed
            if (result != last_result or current_window != last_window):
                print(f"[{time.strftime('%H:%M:%S')}] ", end="")
                
                if result:
                    print("✅ TEXT FIELD DETECTED")
                else:
                    print("❌ NO TEXT FIELD")
                
                print(f"  Window: {current_window}")
                print(f"  Control: {control_class}")
                print(f"  Cursor is I-beam: {info.get('is_ibeam_cursor', 'Unknown')}")
                
                if info.get('error'):
                    print(f"  Error: {info['error']}")
                    
                print()
                
                last_result = result
                last_window = current_window
            
            time.sleep(0.5)  # Check twice per second
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
