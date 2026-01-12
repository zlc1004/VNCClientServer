@echo off
echo Starting VNC QR Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment!
        pause
        exit /b 1
    )
)

REM Git submodules no longer needed for VNC functionality
REM echo Updating git submodules...
REM git submodule update --init --recursive

REM Using explicit venv paths instead of activation

REM Install dependencies
echo Installing dependencies...
.\venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies!
    pause
    exit /b 1
)

echo Checking for VNC clients on Windows...
.\venv\Scripts\python.exe -c "
import sys
import os
import shutil

print('Python version:', sys.version)
print()

# Check for VNC clients
clients_found = []

# Check TightVNC
tight_paths = [
    'C:\\Program Files\\TightVNC\\tvnviewer.exe',
    'C:\\Program Files (x86)\\TightVNC\\tvnviewer.exe'
]
for path in tight_paths:
    if os.path.exists(path):
        clients_found.append(f'TightVNC: {path}')

# Check RealVNC
real_paths = [
    'C:\\Program Files\\RealVNC\\VNC Viewer\\vncviewer.exe',
    'C:\\Program Files (x86)\\RealVNC\\VNC Viewer\\vncviewer.exe'
]
for path in real_paths:
    if os.path.exists(path):
        clients_found.append(f'RealVNC: {path}')

# Check UltraVNC
ultra_paths = [
    'C:\\Program Files\\uvnc bvba\\UltraVNC\\vncviewer.exe',
    'C:\\Program Files (x86)\\uvnc bvba\\UltraVNC\\vncviewer.exe',
    'C:\\Program Files\\UltraVNC\\vncviewer.exe',
    'C:\\Program Files (x86)\\UltraVNC\\vncviewer.exe'
]
for path in ultra_paths:
    if os.path.exists(path):
        clients_found.append(f'UltraVNC: {path}')

# Check PATH
if shutil.which('vncviewer.exe'):
    clients_found.append('VNC Viewer in PATH')
if shutil.which('tvnviewer.exe'):
    clients_found.append('TightVNC Viewer in PATH')

if clients_found:
    print('✅ VNC clients found:')
    for client in clients_found:
        print(f'  - {client}')
    print()
    print('✅ VNC functionality will be available')
else:
    print('❌ No VNC clients detected')
    print('VNC functionality will be limited to QR code display only')
    print()
    print('To enable VNC connections, please install one of the following:')
    print('  - TightVNC: https://www.tightvnc.com/download.php')
    print('  - RealVNC Viewer: https://www.realvnc.com/en/connect/download/viewer/')
    print('  - UltraVNC: https://uvnc.com/downloads/ultravnc.html')
    print()
"

if errorlevel 1 (
    echo Failed to check VNC clients!
    pause
    exit /b 1
)

REM Start the application
echo.
echo Starting VNC QR Server Application...
echo Press Ctrl+C to stop the server
echo.
.\venv\Scripts\python.exe main.py

pause
