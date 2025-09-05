#!/usr/bin/env python3
"""
WindVoice-Windows Build & Installer Script
Creates MSI installer for proper Windows installation
"""

import os
import sys
import subprocess
import shutil
import uuid
from pathlib import Path

def run_command(cmd, description, capture_output=True):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    print(f"Running: {cmd}")
    
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
        else:
            result = subprocess.run(cmd, shell=True, check=True)
            
        print(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} failed!")
        print(f"Error code: {e.returncode}")
        if hasattr(e, 'stdout') and e.stdout:
            print(f"Output: {e.stdout}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error: {e.stderr}")
        return False

def safe_remove_tree(path):
    """Safely remove directory tree with retry"""
    import time
    for attempt in range(3):
        try:
            if path.exists():
                shutil.rmtree(path)
                print(f"Removed {path.name}/ directory")
            return True
        except PermissionError as e:
            if attempt < 2:
                print(f"WARNING: {path.name}/ directory busy, retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"WARNING: Could not remove {path.name}/ directory: {e}")
                print(f"   Please close any running WindVoice processes and try again")
                return False
        except Exception as e:
            print(f"WARNING: Error removing {path.name}/ directory: {e}")
            return False
    return True

def create_wix_installer(app_dir, exe_path):
    """Create MSI installer using WiX Toolset"""
    installer_dir = app_dir / "installer"
    installer_dir.mkdir(exist_ok=True)
    
    # Generate unique GUIDs for WiX
    product_guid = str(uuid.uuid4()).upper()
    upgrade_guid = "12345678-1234-1234-1234-123456789ABC"  # Fixed for upgrades
    
    # Create WiX source file with proper installer UI
    wxs_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
    <Product Id="{product_guid}" 
             Name="WindVoice-Windows" 
             Language="1033" 
             Version="1.0.0.0" 
             Manufacturer="WindVoice Team"
             UpgradeCode="{upgrade_guid}">
             
        <Package InstallerVersion="200" 
                 Compressed="yes" 
                 InstallScope="perMachine" 
                 Description="WindVoice-Windows - Voice dictation application for Windows"
                 Comments="Fast and accurate voice-to-text transcription with automatic text insertion"
                 AdminImage="no"
                 InstallPrivileges="elevated" />

        <MajorUpgrade DowngradeErrorMessage="A newer version of WindVoice-Windows is already installed. Please uninstall the current version before proceeding." />
        
        <MediaTemplate EmbedCab="yes" />
        
        <!-- Include WiX UI Extension for standard dialogs -->
        <UIRef Id="WixUI_InstallDir" />
        <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
        
        <!-- License agreement (using built-in template) -->
        <WixVariable Id="WixUILicenseRtf" Value="License.rtf" />
        
        <!-- Custom properties for installer -->
        <Property Id="ARPHELPLINK" Value="https://github.com/your-repo/windvoice-windows" />
        <Property Id="ARPURLINFOABOUT" Value="https://github.com/your-repo/windvoice-windows" />
        
        <!-- Application information displayed in installer -->
        <Property Id="ApplicationFolderName" Value="WindVoice-Windows" />
        <Property Id="WixAppFolder" Value="WixPerMachineFolder" />

        <Feature Id="ProductFeature" 
                 Title="WindVoice-Windows Application" 
                 Description="Complete WindVoice-Windows voice dictation application with system integration."
                 Level="1"
                 ConfigurableDirectory="INSTALLFOLDER"
                 AllowAdvertise="no"
                 Display="expand"
                 Absent="disallow">
            <ComponentGroupRef Id="ProductComponents" />
            <ComponentGroupRef Id="StartMenuComponents" />
        </Feature>
        
        <!-- Optional auto-start feature -->
        <Feature Id="AutoStartFeature"
                 Title="Start with Windows"
                 Description="Automatically start WindVoice-Windows when Windows starts (recommended)."
                 Level="1"
                 AllowAdvertise="no">
            <ComponentRef Id="AutoStartRegistry" />
        </Feature>
        
        <!-- Installation directories with proper default path -->
        <Directory Id="TARGETDIR" Name="SourceDir">
            <Directory Id="ProgramFilesFolder">
                <Directory Id="INSTALLFOLDER" Name="WindVoice-Windows" />
            </Directory>
            <!-- Start Menu shortcut -->
            <Directory Id="ProgramMenuFolder">
                <Directory Id="ApplicationProgramsFolder" Name="WindVoice-Windows"/>
            </Directory>
        </Directory>

        <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
            <!-- Main executable -->
            <Component Id="MainExecutable" Guid="{str(uuid.uuid4()).upper()}">
                <File Id="WindVoiceExe" 
                      Name="WindVoice-Windows.exe"
                      Source="{exe_path}"
                      KeyPath="yes" />
            </Component>
            
            <!-- Application registry entries -->
            <Component Id="AppRegistry" Guid="{str(uuid.uuid4()).upper()}">
                <RegistryKey Root="HKLM" Key="Software\\WindVoice-Windows">
                    <RegistryValue Name="InstallLocation" Type="string" Value="[INSTALLFOLDER]" KeyPath="yes" />
                    <RegistryValue Name="Version" Type="string" Value="1.0.0.0" />
                    <RegistryValue Name="Publisher" Type="string" Value="WindVoice Team" />
                </RegistryKey>
            </Component>
        </ComponentGroup>
        
        <!-- Auto-start registry entry (separate component) -->
        <Component Id="AutoStartRegistry" Directory="INSTALLFOLDER" Guid="{str(uuid.uuid4()).upper()}">
            <RegistryValue Root="HKCU" 
                          Key="Software\\Microsoft\\Windows\\CurrentVersion\\Run"
                          Name="WindVoice-Windows"
                          Value="[INSTALLFOLDER]WindVoice-Windows.exe"
                          Type="string" 
                          KeyPath="yes" />
        </Component>
        
        <ComponentGroup Id="StartMenuComponents" Directory="ApplicationProgramsFolder">
            <!-- Start Menu shortcut -->
            <Component Id="StartMenuShortcut" Guid="{str(uuid.uuid4()).upper()}">
                <Shortcut Id="ApplicationStartMenuShortcut"
                         Name="WindVoice-Windows"
                         Description="Voice dictation for Windows"
                         Target="[INSTALLFOLDER]WindVoice-Windows.exe"
                         WorkingDirectory="INSTALLFOLDER"/>
                <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall"/>
                <RegistryValue Root="HKCU" Key="Software\\WindVoice-Windows" Name="installed" Type="integer" Value="1" KeyPath="yes"/>
            </Component>
        </ComponentGroup>
    </Product>
</Wix>'''
    
    wxs_file = installer_dir / "WindVoice.wxs"
    wxs_file.write_text(wxs_content, encoding='utf-8')
    
    print(f"Created WiX source: {wxs_file}")
    
    # Check if WiX is installed
    wix_candle = shutil.which('candle')
    wix_light = shutil.which('light')
    
    if not wix_candle or not wix_light:
        print("\nWiX Toolset not found. Installing WiX...")
        print("Please install WiX Toolset v3 from: https://wixtoolset.org/releases/")
        print("After installation, restart your command prompt and run this script again.")
        return False
    
    # Compile WiX source to object file
    wixobj_file = installer_dir / "WindVoice.wixobj"
    candle_cmd = f'candle -out "{wixobj_file}" "{wxs_file}"'
    
    if not run_command(candle_cmd, "Compiling WiX source"):
        return False
    
    # Create license file
    license_file = installer_dir / "License.rtf"
    license_content = r'''{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}
\f0\fs24
WindVoice-Windows License Agreement\par
\par
Copyright (c) 2024 WindVoice Team\par
\par
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\par
\par
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\par
\par
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\par
}'''
    
    license_file.write_text(license_content, encoding='utf-8')
    print(f"Created license file: {license_file}")
    
    # Link object file to create MSI with UI extension
    msi_file = installer_dir / "WindVoice-Windows-Installer.msi"
    light_cmd = f'light -ext WixUIExtension -out "{msi_file}" "{wixobj_file}"'
    
    if not run_command(light_cmd, "Creating MSI installer"):
        return False
    
    if msi_file.exists():
        msi_size = msi_file.stat().st_size / (1024 * 1024)
        print(f"\nMSI Installer created successfully!")
        print(f"Installer: {msi_file}")
        print(f"Size: {msi_size:.1f} MB")
        return msi_file
    else:
        print("MSI installer not found after build")
        return False

def main():
    """Main build process"""
    app_dir = Path(__file__).parent
    dist_dir = app_dir / "dist"
    build_dir = app_dir / "build"
    
    print("WindVoice-Windows Build & Installer Script")
    print("=" * 60)
    
    # Clean previous builds
    print("\nCleaning previous builds...")
    safe_remove_tree(dist_dir)
    safe_remove_tree(build_dir)
    safe_remove_tree(app_dir / "installer")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("PyInstaller not found. Installing...")
        if not run_command("pip install pyinstaller", "PyInstaller installation"):
            return False
    
    # Check if all dependencies are installed
    print("\nChecking dependencies...")
    required_packages = [
        'customtkinter', 'sounddevice', 'soundfile', 'numpy', 'scipy',
        'pynput', 'pystray', 'pyperclip', 'aiohttp', 'tomli-w', 'Pillow', 'pywin32'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"{package}")
        except ImportError:
            missing_packages.append(package)
            print(f"MISSING: {package}")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        packages_str = ' '.join(missing_packages)
        if not run_command(f"pip install {packages_str}", "Installing missing dependencies"):
            return False
    
    # Build the executable
    spec_file = app_dir / "WindVoice.spec"
    if not spec_file.exists():
        print(f"Spec file not found: {spec_file}")
        return False
    
    build_cmd = f'pyinstaller "{spec_file}" --clean --noconfirm'
    if not run_command(build_cmd, "Building executable with PyInstaller"):
        return False
    
    # Check if executable was created
    exe_path = dist_dir / "WindVoice-Windows.exe"
    if exe_path.exists():
        exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"\nExecutable build completed!")
        print(f"Executable: {exe_path}")
        print(f"Size: {exe_size:.1f} MB")
        
        # Create MSI installer
        print("\nCreating MSI installer...")
        msi_path = create_wix_installer(app_dir, exe_path)
        
        if msi_path:
            print("\n" + "="*60)
            print("[SUCCESS] WindVoice-Windows Installer Created Successfully!")
            print("="*60)
            print(f"MSI Installer: {msi_path}")
            print(f"Size: {msi_path.stat().st_size / (1024 * 1024):.1f} MB")
            print("\nInstallation Instructions:")
            print("   1. Double-click the MSI file to start installation")
            print("   2. Follow the installation wizard:")
            print("      - Welcome screen with application description")
            print("      - License agreement acceptance")
            print("      - Choose installation directory (default: Program Files)")
            print("      - Select features (App + Auto-start with Windows)")
            print("      - Installation progress and completion")
            print("   3. After installation:")
            print("      - Find 'WindVoice-Windows' in Start Menu")
            print("      - App will auto-start with Windows (if selected)")
            print("      - Use Ctrl+Shift+Space hotkey for voice dictation")
            print("\nFeatures included:")
            print("   [X] Professional Windows installer experience")
            print("   [X] Start Menu integration")  
            print("   [X] Optional auto-start with Windows")
            print("   [X] Proper uninstall support")
            print("   [X] System integration for any Windows app")
            print("="*60)
        else:
            print("\n[ERROR] MSI creation failed, but executable is available")
            print(f"Executable: {exe_path}")
            print("   You can still run WindVoice-Windows directly from the .exe file")
        
        return True
    else:
        print(f"Executable not found at expected location: {exe_path}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)