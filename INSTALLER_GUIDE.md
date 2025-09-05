# WindVoice-Windows Installer Guide

## Overview

WindVoice-Windows now includes a professional MSI installer that provides proper Windows installation with:

- ✅ **Automatic startup with Windows**
- ✅ **Start Menu shortcuts**
- ✅ **Proper installation to AppData**
- ✅ **Clean uninstallation via Windows Settings**
- ✅ **First-time setup wizard for new users**
- ✅ **No pre-configured credentials**

## Quick Start

### 1. Build the Installer

```bash
# Install WiX Toolset (if not already installed)
python install_wix.py

# Build MSI installer
python build.py
```

### 2. Install WindVoice

```bash
# Double-click the generated MSI file
installer/WindVoice-Windows-Installer.msi
```

### 3. Complete Setup

- The application will launch a setup wizard on first run
- Enter your Thomson Reuters LiteLLM credentials
- Choose your preferences (theme, notifications)
- Start using WindVoice with `Ctrl+Shift+Space`

## Detailed Instructions

### Step 1: Prerequisites

Ensure you have:
- Python 3.10+ installed
- All project dependencies: `pip install -r requirements.txt`
- WiX Toolset v3.11+ (auto-installed by our script)

### Step 2: Install WiX Toolset (First Time Only)

```bash
python install_wix.py
```

This script will:
- Check if WiX is already installed
- Download WiX Toolset v3.11.2 if needed
- Install it with admin privileges
- Verify the installation

**Manual Installation Alternative:**
1. Download from: https://wixtoolset.org/releases/
2. Install WiX Toolset v3.11.2
3. Restart your command prompt

### Step 3: Build the Installer

```bash
python build.py
```

This will:
1. Clean previous builds
2. Check dependencies
3. Build the executable with PyInstaller
4. Create MSI installer with WiX Toolset
5. Output: `installer/WindVoice-Windows-Installer.msi`

### Step 4: Install on Target Machine

1. **Copy the MSI file** to the target Windows 10/11 machine
2. **Double-click** `WindVoice-Windows-Installer.msi`
3. **Follow the installation wizard**
4. **Application installs to:** `%LOCALAPPDATA%\WindVoice-Windows\`
5. **Start Menu shortcut created**
6. **Auto-start with Windows enabled**

### Step 5: First-Time Setup

When WindVoice runs for the first time:

1. **Setup Wizard launches automatically**
2. **Enter your LiteLLM credentials:**
   - API Key (sk-xxxxx)
   - API Base URL (https://your-proxy.com)
   - User ID / Key Alias
3. **Choose preferences:**
   - Interface theme (Dark/Light)
   - System tray notifications
4. **Complete setup** - WindVoice starts immediately

## Installation Features

### What Gets Installed

- **Main Application:** `WindVoice-Windows.exe`
- **Location:** `%LOCALAPPDATA%\WindVoice-Windows\`
- **Start Menu:** "WindVoice-Windows" shortcut
- **Registry:** Auto-start entry in Windows startup
- **Configuration:** Clean slate - no pre-configured credentials

### Auto-Start Behavior

- WindVoice starts automatically when Windows boots
- Runs silently in system tray
- No visible windows - just the tray icon
- Press `Ctrl+Shift+Space` to start voice recording

### Uninstallation

**Via Windows Settings:**
1. Windows Settings → Apps → WindVoice-Windows → Uninstall

**Via Control Panel:**
1. Control Panel → Programs → Uninstall a program → WindVoice-Windows

**What Gets Removed:**
- Application files
- Start Menu shortcuts
- Registry auto-start entries
- **Note:** User configuration in `~/.windvoice/` is preserved

## Troubleshooting

### Build Issues

**"WiX Toolset not found"**
```bash
python install_wix.py
```

**"PyInstaller failed"**
```bash
pip install --upgrade pyinstaller
python build.py
```

**"Permission denied"**
- Run command prompt as Administrator
- Close any running WindVoice processes

### Installation Issues

**"Cannot install MSI"**
- Right-click MSI → "Run as administrator"
- Check Windows Defender/antivirus settings

**"Setup wizard doesn't appear"**
- Delete `%USERPROFILE%\.windvoice\.setup_completed`
- Restart WindVoice

### Runtime Issues

**"Application won't start"**
- Check Start Menu → WindVoice-Windows
- Or run directly: `%LOCALAPPDATA%\WindVoice-Windows\WindVoice-Windows.exe`

**"Microphone not working"**
- Right-click tray icon → Settings
- Test microphone and select different device

## Advanced Options

### Custom Installation

You can modify the WiX installer by editing the generated `installer/WindVoice.wxs` file before running the light command.

### Development Testing

For development, you can still use the portable executable:
```bash
pyinstaller WindVoice.spec --clean --noconfirm
dist/WindVoice-Windows.exe
```

### Corporate Deployment

The MSI installer supports silent installation:
```bash
msiexec /i WindVoice-Windows-Installer.msi /quiet
```

## File Structure After Build

```
project/
├── build.py                              # Main build script
├── install_wix.py                        # WiX installer script
├── dist/
│   └── WindVoice-Windows.exe             # Portable executable
├── installer/
│   ├── WindVoice.wxs                     # WiX source file
│   ├── WindVoice.wixobj                  # Compiled object
│   └── WindVoice-Windows-Installer.msi   # Final MSI installer
└── INSTALLER_GUIDE.md                    # This guide
```

## Success Checklist

After installation, verify:

- [ ] WindVoice icon appears in system tray
- [ ] `Ctrl+Shift+Space` starts recording
- [ ] Setup wizard completed with your credentials
- [ ] Application auto-starts after Windows reboot
- [ ] Start Menu shortcut works
- [ ] Uninstaller works properly

## Support

If you encounter issues:

1. Check this guide first
2. Look at console output during build
3. Check Windows Event Viewer for installation errors
4. Verify WiX Toolset installation: `candle /?`

---

**Note:** This installer creates a clean, professional Windows installation that follows Microsoft guidelines and user expectations.