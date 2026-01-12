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

REM Create temporary Python script for VNC client detection
echo import sys > temp_vnc_check.py
echo import os >> temp_vnc_check.py
echo import shutil >> temp_vnc_check.py
echo. >> temp_vnc_check.py
echo print('Python version:', sys.version^) >> temp_vnc_check.py
echo print(^) >> temp_vnc_check.py
echo. >> temp_vnc_check.py
echo # Check for VNC clients >> temp_vnc_check.py
echo clients_found = [] >> temp_vnc_check.py
echo. >> temp_vnc_check.py
echo # Check TightVNC >> temp_vnc_check.py
echo tight_paths = [ >> temp_vnc_check.py
echo     'C:\\\\Program Files\\\\TightVNC\\\\tvnviewer.exe', >> temp_vnc_check.py
echo     'C:\\\\Program Files ^(x86^)\\\\TightVNC\\\\tvnviewer.exe' >> temp_vnc_check.py
echo ] >> temp_vnc_check.py
echo for path in tight_paths: >> temp_vnc_check.py
echo     if os.path.exists(path^): >> temp_vnc_check.py
echo         clients_found.append(f'TightVNC: {path}'^) >> temp_vnc_check.py
echo. >> temp_vnc_check.py
echo # Check RealVNC >> temp_vnc_check.py
echo real_paths = [ >> temp_vnc_check.py
echo     'C:\\\\Program Files\\\\RealVNC\\\\VNC Viewer\\\\vncviewer.exe', >> temp_vnc_check.py
echo     'C:\\\\Program Files ^(x86^)\\\\RealVNC\\\\VNC Viewer\\\\vncviewer.exe' >> temp_vnc_check.py
echo ] >> temp_vnc_check.py
echo for path in real_paths: >> temp_vnc_check.py
echo     if os.path.exists(path^): >> temp_vnc_check.py
echo         clients_found.append(f'RealVNC: {path}'^) >> temp_vnc_check.py
echo. >> temp_vnc_check.py
echo # Check UltraVNC >> temp_vnc_check.py
echo ultra_paths = [ >> temp_vnc_check.py
echo     'C:\\\\Program Files\\\\uvnc bvba\\\\UltraVNC\\\\vncviewer.exe', >> temp_vnc_check.py
echo     'C:\\\\Program Files ^(x86^)\\\\uvnc bvba\\\\UltraVNC\\\\vncviewer.exe', >> temp_vnc_check.py
echo     'C:\\\\Program Files\\\\UltraVNC\\\\vncviewer.exe', >> temp_vnc_check.py
echo     'C:\\\\Program Files ^(x86^)\\\\UltraVNC\\\\vncviewer.exe' >> temp_vnc_check.py
echo ] >> temp_vnc_check.py
echo for path in ultra_paths: >> temp_vnc_check.py
echo     if os.path.exists(path^): >> temp_vnc_check.py
echo         clients_found.append(f'UltraVNC: {path}'^) >> temp_vnc_check.py
echo. >> temp_vnc_check.py
echo # Check PATH >> temp_vnc_check.py
echo if shutil.which('vncviewer.exe'^): >> temp_vnc_check.py
echo     clients_found.append('VNC Viewer in PATH'^) >> temp_vnc_check.py
echo if shutil.which('tvnviewer.exe'^): >> temp_vnc_check.py
echo     clients_found.append('TightVNC Viewer in PATH'^) >> temp_vnc_check.py
echo. >> temp_vnc_check.py
echo if clients_found: >> temp_vnc_check.py
echo     print('✅ VNC clients found:'^) >> temp_vnc_check.py
echo     for client in clients_found: >> temp_vnc_check.py
echo         print(f'  - {client}'^) >> temp_vnc_check.py
echo     print(^) >> temp_vnc_check.py
echo     print('✅ VNC functionality will be available'^) >> temp_vnc_check.py
echo else: >> temp_vnc_check.py
echo     print('❌ No VNC clients detected'^) >> temp_vnc_check.py
echo     print('VNC functionality will be limited to QR code display only'^) >> temp_vnc_check.py
echo     print(^) >> temp_vnc_check.py
echo     print('To enable VNC connections, please install one of the following:'^) >> temp_vnc_check.py
echo     print('  - TightVNC: https://www.tightvnc.com/download.php'^) >> temp_vnc_check.py
echo     print('  - RealVNC Viewer: https://www.realvnc.com/en/connect/download/viewer/'^) >> temp_vnc_check.py
echo     print('  - UltraVNC: https://uvnc.com/downloads/ultravnc.html'^) >> temp_vnc_check.py
echo     print(^) >> temp_vnc_check.py

REM Execute the temporary Python script
.\venv\Scripts\python.exe temp_vnc_check.py

REM Clean up temporary file
del temp_vnc_check.py

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
