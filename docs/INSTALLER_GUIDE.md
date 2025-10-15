# WindVoice-Windows Installation Guide

## Overview

WindVoice-Windows provides multiple installation methods with robust error handling and automatic configuration detection to ensure a smooth installation experience.

## Installation Methods

### 1. Portable Executable (Recommended for Most Users)

**Best for:** General users, corporate environments with permission restrictions, portable deployment

The standalone executable runs immediately without installation and avoids admin privilege requirements.

#### Building the Executable

```bash
git clone <repository-url>
cd WindVoice-Windows
pyinstaller WindVoice.spec --clean --noconfirm
```

**Executable Location:** `dist/WindVoice-Windows.exe`

#### Benefits

- ✅ No installation or admin privileges required
- ✅ Portable - run from any folder or USB drive
- ✅ No uninstall issues - just delete the file
- ✅ Corporate friendly - bypasses installation policies
- ✅ Built-in configuration tools (`--check-config`, `--create-config`)

> **Why EXE?** MSI installers may install successfully but require admin privileges to uninstall, potentially leaving systems in a blocked state.

### 2. MSI Installer (For System Integration)

**Best for:** Users with admin access who want full system integration (Start Menu, auto-start, registry integration)

#### Prerequisites & Building

```bash
# Install WiX Toolset (required for MSI compilation)
python install_wix.py

# Build MSI installer
python build.py
```

**MSI Location:** `installer/WindVoice-Windows-Installer.msi`

#### Installation

1. Double-click `WindVoice-Windows-Installer.msi`
2. Follow setup wizard (welcome, license, directory, features)
3. Launch from Start Menu

#### Features

- ✅ Start Menu integration with shortcuts
- ✅ Auto-start with Windows (optional)
- ✅ Registry integration
- ✅ Professional uninstall via Programs & Features
- ❗ **Requires admin privileges for uninstallation**

> **⚠️ Warning:** Only use MSI if you have full admin access. MSI may install successfully but require admin privileges to uninstall.

### 3. Python Development Installation

**Best for:** Developers and contributors

```bash
git clone <repository-url>
cd WindVoice-Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**See:** [DEVELOPMENT.md](DEVELOPMENT.md) for complete development setup

## Initial Configuration

### Automatic Setup Wizard

On first launch, WindVoice detects missing configuration and launches the setup wizard:

1. **Welcome Screen** → API Configuration → Preferences → Completion

### Manual Configuration

Use emergency configuration tools or edit config file directly:

```bash
# Check configuration status
WindVoice-Windows.exe --check-config

# Create configuration template
WindVoice-Windows.exe --create-config
```

**Configuration file location:** `%USERPROFILE%\.windvoice\config.toml`

**See:** [config.example.toml](config.example.toml) for complete configuration reference with descriptions

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