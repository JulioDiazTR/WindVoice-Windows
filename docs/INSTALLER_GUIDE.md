# WindVoice-Windows Installation Guide

## Overview

WindVoice-Windows provides multiple installation methods with robust error handling and automatic configuration detection to ensure a smooth installation experience.

## Installation Methods

### 1. Portable Executable (Recommended)

The standalone executable provides immediate deployment without installation requirements or admin privilege concerns.

#### Building the Portable Executable

```bash
# Clone and build
git clone <repository-url>
cd WindVoice-Windows

# Build standalone executable
pyinstaller WindVoice.spec --clean --noconfirm
```

#### Running the Executable

1. **Navigate to** `dist/` folder
2. **Double-click** `WindVoice-Windows.exe`
3. **No installation required** - runs immediately

#### Portable Executable Features

- ✅ **No Installation Required**: Run directly from any folder
- ✅ **No Admin Privileges**: Bypass organizational permission restrictions
- ✅ **Portable Deployment**: Move to any Windows system
- ✅ **No Uninstall Issues**: Simply delete when no longer needed
- ✅ **Emergency Configuration**: Built-in configuration tools
- ✅ **Corporate Friendly**: Avoid installation policy conflicts

> **Why Portable EXE is recommended:** Due to organizational permission policies, MSI installers may install successfully but cannot be uninstalled without admin privileges, potentially leaving systems in a blocked state. The portable executable avoids these issues entirely.

### 2. MSI Installer (Alternative)

The MSI installer provides a professional Windows installation experience but may require admin privileges for uninstallation.

#### Building the MSI Installer

**Prerequisites:**
- Python 3.10+
- WiX Toolset v3.11+ (Windows Installer XML)

**Build Process:**
```bash
# Clone and build
git clone <repository-url>
cd WindVoice-Windows

# Install WiX Toolset (required for MSI)
python install_wix.py

# Build complete distribution
python build.py
```

**WiX Toolset Installation:**
The MSI installer requires WiX Toolset to compile Windows Installer packages:
- **Automatic**: `python install_wix.py` (recommended)
- **Manual**: Download from [https://wixtoolset.org/releases/](https://wixtoolset.org/releases/)
- **Verify**: Run `candle -?` and `light -?` to confirm installation

#### Installation Process

1. **Double-click** `installer/WindVoice-Windows-Installer.msi`
2. **Setup Wizard** will guide you through:
   - Welcome screen with application description
   - License agreement (MIT License)  
   - Installation directory selection (default: Program Files)
   - Feature selection:
     - ✅ WindVoice-Windows Application (required)
     - ✅ Start with Windows (optional, recommended)
   - Installation progress with real-time feedback
   - Completion confirmation

3. **Launch Application**
   - Find "WindVoice-Windows" in Start Menu
   - Or navigate to installation directory

#### MSI Installer Features

- ✅ **Professional UI**: Standard Windows installer dialogs
- ✅ **Start Menu Integration**: Desktop shortcuts and Start Menu entries
- ✅ **Auto-start Option**: Launch with Windows (optional)
- ✅ **Proper Uninstall**: Full removal via Programs & Features
- ✅ **Upgrade Support**: In-place upgrades for future versions
- ✅ **Registry Integration**: Proper Windows application registration

### 2. MSI Installer Features (Advanced Users)

> **⚠️ Warning:** MSI installation may require admin privileges for uninstallation. Use only if you have full admin access or prefer system integration.

### 3. Python Package (Development)

For developers and advanced users.

```bash
git clone <repository-url>
cd WindVoice-Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Initial Configuration

### Automatic Setup Wizard

On first launch, WindVoice automatically detects if configuration is needed and launches the setup wizard:

1. **Welcome Screen**: Introduction and feature overview
2. **API Configuration**: Thomson Reuters LiteLLM credentials
3. **Preferences**: Theme selection and notification settings
4. **Completion**: Automatic configuration save and setup marker creation

### Manual Configuration

If the setup wizard doesn't appear or you prefer manual setup:

#### Emergency Configuration Tools

```bash
# Check current configuration status
WindVoice-Windows.exe --check-config

# Create emergency configuration template
WindVoice-Windows.exe --create-config
```

#### Configuration File

Edit `%USERPROFILE%\.windvoice\config.toml`:

```toml
[litellm]
api_key = "sk-your-litellm-api-key"
api_base = "https://your-litellm-proxy.com"
key_alias = "your-username"
model = "whisper-1"

[app]
hotkey = "ctrl+shift+space"
audio_device = "default"
sample_rate = 44100

[ui]
theme = "dark"
window_position = "center"
show_tray_notifications = true
```

## Troubleshooting Installation Issues

### Problem: Application Closes Immediately

**Symptoms:** Brief window flash, no system tray icon

**Automatic Fix:** WindVoice now automatically detects valid configurations and creates missing setup markers.

**Manual Fix:**
```bash
WindVoice-Windows.exe --check-config
WindVoice-Windows.exe --create-config  # If needed
```

### Problem: Setup Wizard Doesn't Appear

**Symptoms:** Application launches but no setup window shows

**Solutions:**
1. Check if running in headless environment (no GUI)
2. Use emergency configuration: `--create-config`
3. Manually edit configuration file
4. Ensure proper Windows desktop environment

### Problem: MSI Installation Fails

**Common Causes:**
- Insufficient privileges
- Previous installation conflicts
- Corrupted installer file

**Solutions:**
1. Run as Administrator
2. Uninstall previous versions first
3. Re-download/rebuild installer
4. Check Windows Event Log for detailed errors

### Problem: Configuration Not Detected

**Symptoms:** "Configuration required but setup wizard unavailable"

**Automatic Recovery:**
- WindVoice automatically detects existing valid configurations
- Creates missing `.setup_completed` marker files
- Provides manual setup guidance when GUI unavailable

**Manual Recovery:**
```bash
# Diagnose the issue
WindVoice-Windows.exe --check-config

# Create template if needed
WindVoice-Windows.exe --create-config
```

## Advanced Installation Scenarios

### Corporate/Enterprise Deployment

1. **Silent MSI Installation:**
   ```cmd
   msiexec /i WindVoice-Windows-Installer.msi /quiet
   ```

2. **Pre-configured Deployment:**
   - Deploy with pre-configured `config.toml`
   - Include `.setup_completed` marker file
   - Use Group Policy for consistent settings

### Headless/Server Environments

For environments without GUI support:

1. **Pre-create Configuration:**
   ```bash
   # Create config directory
   mkdir %USERPROFILE%\.windvoice
   
   # Copy pre-configured config.toml
   copy config-template.toml %USERPROFILE%\.windvoice\config.toml
   
   # Create setup completion marker
   echo. > %USERPROFILE%\.windvoice\.setup_completed
   ```

2. **Use Emergency Tools:**
   ```bash
   WindVoice-Windows.exe --create-config
   # Edit generated config.toml with actual credentials
   ```

## Post-Installation Verification

### Verify Installation

```bash
# Check all installation components
WindVoice-Windows.exe --check-config
```

**Expected Output:**
```
WindVoice-Windows Configuration Status
========================================
Config directory: C:\Users\[username]\.windvoice
Config file: [OK] Exists
Setup completed: [OK] Yes
Valid credentials: [OK] Yes
```

### Test Functionality

1. **Launch Application**: Look for system tray icon
2. **Test Hotkey**: Press `Ctrl+Shift+Space`
3. **Check Settings**: Right-click tray icon → Settings
4. **Verify Audio**: Record a brief test message

## Uninstallation

### MSI Installation
- **Programs & Features**: Control Panel → Programs → WindVoice-Windows → Uninstall
- **Settings App**: Apps → WindVoice-Windows → Uninstall

### Manual Cleanup (if needed)
```cmd
# Remove application files
rmdir /s "C:\Program Files\WindVoice-Windows"

# Remove user configuration
rmdir /s "%USERPROFILE%\.windvoice"

# Remove auto-start registry entry
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindVoice-Windows" /f
```

## Support and Diagnostics

For installation issues:

1. **Run Diagnostics:**
   ```bash
   WindVoice-Windows.exe --check-config
   ```

2. **Enable Debug Logging:**
   ```bash
   set WINDVOICE_LOG_LEVEL=DEBUG
   WindVoice-Windows.exe
   ```

3. **Check Log Files:**
   - Location: `%USERPROFILE%\.windvoice\logs\`
   - Review for installation and configuration errors

4. **Report Issues:**
   Include output from `--check-config` and relevant log excerpts (remove sensitive data).