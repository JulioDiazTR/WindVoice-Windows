#!/usr/bin/env python3
"""
WindVoice-Windows Main Entry Point

Native Windows voice dictation application with global hotkey support.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from windvoice.core.app import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWindVoice stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"WindVoice failed to start: {e}")
        sys.exit(1)