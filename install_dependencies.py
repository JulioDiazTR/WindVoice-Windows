#!/usr/bin/env python3
"""
WindVoice-Windows Dependency Installation Script

Installs all required dependencies for WindVoice-Windows with proper error handling
and Windows-specific optimizations.
"""

import sys
import subprocess
import os
from pathlib import Path
import pkg_resources


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version}")
        return True


def install_package(package_name: str, upgrade: bool = False) -> bool:
    """Install a single package with error handling"""
    try:
        cmd = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package_name)
        
        print(f"Installing {package_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully installed {package_name}")
            return True
        else:
            print(f"❌ Failed to install {package_name}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing {package_name}: {e}")
        return False


def check_package_installed(package_name: str) -> bool:
    """Check if a package is already installed"""
    try:
        pkg_resources.get_distribution(package_name.split('>=')[0].split('==')[0])
        return True
    except pkg_resources.DistributionNotFound:
        return False


def install_dependencies():
    """Install all dependencies from requirements.txt"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print(f"📦 Installing dependencies from {requirements_file}")
    
    # Read requirements
    with open(requirements_file, 'r') as f:
        lines = f.readlines()
    
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            packages.append(line)
    
    print(f"Found {len(packages)} packages to install")
    
    failed_packages = []
    installed_packages = []
    
    for package in packages:
        if check_package_installed(package):
            print(f"✅ {package} already installed")
            installed_packages.append(package)
        else:
            if install_package(package):
                installed_packages.append(package)
            else:
                failed_packages.append(package)
    
    # Summary
    print("\n" + "="*50)
    print("INSTALLATION SUMMARY")
    print("="*50)
    print(f"✅ Successfully installed: {len(installed_packages)}")
    for pkg in installed_packages:
        print(f"   - {pkg}")
    
    if failed_packages:
        print(f"\n❌ Failed to install: {len(failed_packages)}")
        for pkg in failed_packages:
            print(f"   - {pkg}")
        return False
    else:
        print("\n🎉 All dependencies installed successfully!")
        return True


def install_windows_specific():
    """Install Windows-specific packages"""
    print("\n🪟 Installing Windows-specific packages...")
    
    windows_packages = [
        "pywin32",  # For Windows API access
    ]
    
    if sys.platform == "win32":
        for package in windows_packages:
            if not check_package_installed(package):
                install_package(package)
    else:
        print("⚠️ Not running on Windows - skipping Windows-specific packages")


def verify_installation():
    """Verify that all critical packages can be imported"""
    print("\n🔍 Verifying installation...")
    
    critical_imports = [
        ("sounddevice", "sd"),
        ("soundfile", "sf"),
        ("numpy", "np"),
        ("scipy", "scipy"),
        ("customtkinter", "ctk"),
        ("pynput", "pynput"),
        ("pystray", "pystray"),
        ("pyperclip", "pyperclip"),
        ("aiohttp", "aiohttp"),
        ("PIL", "PIL"),
    ]
    
    failed_imports = []
    
    for package_name, import_name in critical_imports:
        try:
            __import__(import_name)
            print(f"✅ {package_name} import successful")
        except ImportError as e:
            print(f"❌ {package_name} import failed: {e}")
            failed_imports.append(package_name)
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} packages failed to import")
        print("Please check your installation and try again.")
        return False
    else:
        print("\n✅ All critical packages verified successfully!")
        return True


def test_audio_system():
    """Test if audio system is working"""
    print("\n🎤 Testing audio system...")
    
    try:
        import sounddevice as sd
        
        # Query available devices
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        print(f"Found {len(input_devices)} audio input devices:")
        for i, device in enumerate(input_devices[:3]):  # Show first 3
            print(f"   {i}: {device['name']}")
        
        if input_devices:
            print("✅ Audio system appears to be working")
            return True
        else:
            print("⚠️ No audio input devices found")
            return False
            
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        return False


def main():
    """Main installation process"""
    print("🚀 WindVoice-Windows Dependency Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Upgrade pip first
    print("\n📦 Upgrading pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                  capture_output=True)
    
    # Install main dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed")
        sys.exit(1)
    
    # Install Windows-specific packages
    install_windows_specific()
    
    # Verify installation
    if not verify_installation():
        print("\n❌ Installation verification failed")
        sys.exit(1)
    
    # Test audio system
    test_audio_system()
    
    print("\n" + "=" * 50)
    print("🎉 INSTALLATION COMPLETE!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Configure your LiteLLM API credentials:")
    print("   python setup_config.py")
    print("\n2. Run WindVoice:")
    print("   python main.py")
    print("\n3. If you encounter issues, check the audio folder:")
    print("   Right-click system tray → Settings → Open Audio Folder")


if __name__ == "__main__":
    main()