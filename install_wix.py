#!/usr/bin/env python3
"""
WiX Toolset Installer for WindVoice-Windows
Automatically downloads and installs WiX Toolset v3 for MSI creation
"""

import os
import sys
import subprocess
import tempfile
import urllib.request
from pathlib import Path
import shutil

# WiX Toolset v3.11.2 (stable version for Windows 10/11)
WIX_DOWNLOAD_URL = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311.exe"
WIX_INSTALLER_NAME = "wix311.exe"

def check_wix_installed():
    """Check if WiX Toolset is already installed"""
    print("Checking if WiX Toolset is already installed...")
    
    # Check common installation paths
    common_paths = [
        r"C:\Program Files (x86)\WiX Toolset v3.11\bin",
        r"C:\Program Files\WiX Toolset v3.11\bin",
        Path.home() / "AppData" / "Local" / "WixToolset" / "bin",
    ]
    
    for path in common_paths:
        candle_path = Path(path) / "candle.exe"
        light_path = Path(path) / "light.exe"
        
        if candle_path.exists() and light_path.exists():
            print(f"WiX Toolset found at: {path}")
            
            # Add to PATH if not already there
            current_path = os.environ.get('PATH', '')
            if str(path) not in current_path:
                print(f"Adding WiX to PATH: {path}")
                os.environ['PATH'] = f"{path};{current_path}"
            
            return True
    
    # Check if in PATH
    if shutil.which('candle') and shutil.which('light'):
        print("WiX Toolset found in PATH")
        return True
    
    print("WiX Toolset not found")
    return False

def download_wix_installer():
    """Download WiX Toolset installer"""
    print(f"Downloading WiX Toolset installer from {WIX_DOWNLOAD_URL}...")
    
    temp_dir = Path(tempfile.gettempdir())
    installer_path = temp_dir / WIX_INSTALLER_NAME
    
    try:
        # Download with progress
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                sys.stdout.write(f"\rDownloading... {percent}%")
                sys.stdout.flush()
        
        urllib.request.urlretrieve(WIX_DOWNLOAD_URL, installer_path, progress_hook)
        print(f"\nDownloaded to: {installer_path}")
        return installer_path
        
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return None

def install_wix(installer_path):
    """Install WiX Toolset"""
    print(f"Installing WiX Toolset from {installer_path}...")
    print("This will open the WiX installer. Please follow the installation prompts.")
    print("   Choose 'Complete' installation for all features.")
    
    try:
        # Run installer with admin privileges
        cmd = f'powershell -Command "Start-Process -FilePath \\"{installer_path}\\" -Verb RunAs -Wait"'
        
        print("Running installer (this may take a few minutes)...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("WiX Toolset installer completed")
            return True
        else:
            print(f"Installer failed with return code: {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Installation failed: {e}")
        return False

def verify_installation():
    """Verify WiX installation was successful"""
    print("Verifying WiX installation...")
    
    # Wait a moment for installation to complete
    import time
    time.sleep(2)
    
    # Re-check installation
    return check_wix_installed()

def main():
    print("WiX Toolset Installation Script")
    print("=" * 50)
    print("This script will install WiX Toolset v3.11 for creating MSI installers.")
    print()
    
    # Check if already installed
    if check_wix_installed():
        print("WiX Toolset is already installed and ready to use!")
        print("You can now run: python build.py")
        return True
    
    print()
    print("WiX Toolset is required for creating MSI installers.")
    response = input("Do you want to download and install WiX Toolset? (y/N): ")
    
    if response.lower() not in ['y', 'yes']:
        print("Installation cancelled.")
        print("Note: You can install WiX manually from: https://wixtoolset.org/releases/")
        return False
    
    # Download installer
    installer_path = download_wix_installer()
    if not installer_path:
        print("Failed to download WiX installer.")
        return False
    
    # Install
    if not install_wix(installer_path):
        print("Installation failed.")
        return False
    
    # Verify
    if verify_installation():
        print()
        print("WiX Toolset installation completed successfully!")
        print("You can now run: python build.py")
        
        # Clean up installer
        try:
            installer_path.unlink()
            print("Cleaned up temporary installer file.")
        except:
            pass
        
        return True
    else:
        print()
        print("Installation verification failed.")
        print("Please try installing WiX manually from: https://wixtoolset.org/releases/")
        print("Or restart your command prompt and try running this script again.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)