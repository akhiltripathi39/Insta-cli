# instagram-cli Windows Installation Script (PowerShell)
# Run in PowerShell: Set-ExecutionPolicy Bypass -Scope Process; .\install.ps1

$ErrorActionPreference = "Stop"

$AppName = "insta-cli"
$InstallDir = "$env:LOCALAPPDATA\instagram-cli"
$BinDir = "$InstallDir\bin"
$VenvDir = "$InstallDir\venv"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Installing instagram-cli on Windows..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in your PATH." -ForegroundColor Red
    Write-Host "Please install Python from python.org and check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    exit 1
}

# 2. Create Target Directories
Write-Host "Creating directories at $InstallDir..." -ForegroundColor Gray
if (!(Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}
if (!(Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

# 3. Copy Source Files
Write-Host "Copying source code..." -ForegroundColor Gray
if (Test-Path "$InstallDir\src") {
    Remove-Item -Recurse -Force "$InstallDir\src" | Out-Null
}
Copy-Item -Recurse "src" "$InstallDir\"
Copy-Item "requirements.txt" "$InstallDir\"

if (Test-Path "ascii.txt") {
    Copy-Item "ascii.txt" "$InstallDir\"
}

# 4. Set up Virtual Environment
Write-Host "Setting up Python virtual environment..." -ForegroundColor Gray
python -m venv $VenvDir

# 5. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Gray
& "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip | Out-Null
& "$VenvDir\Scripts\pip.exe" install -r "$InstallDir\requirements.txt"

# 6. Create Wrapper Batch Script
Write-Host "Creating command launcher at $BinDir\$AppName.cmd..." -ForegroundColor Gray
$launcherContent = @"
@echo off
set PYTHONPATH=$InstallDir
"$VenvDir\Scripts\python.exe" -m src.cli %*
"@

Set-Content -Path "$BinDir\$AppName.cmd" -Value $launcherContent

# 7. Add to User Path Environment Variable
Write-Host "Configuring system PATH environment variable..." -ForegroundColor Gray
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    $newPath = $userPath
    if (!$newPath.EndsWith(";")) {
        $newPath += ";"
    }
    $newPath += "$BinDir"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Added $BinDir to User PATH." -ForegroundColor Green
    Write-Host "NOTE: You may need to restart your terminal (e.g., PowerShell/Command Prompt) for the changes to take effect." -ForegroundColor Yellow
} else {
    Write-Host "$BinDir is already in your PATH." -ForegroundColor Green
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Installation Complete! You can now type: $AppName" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
