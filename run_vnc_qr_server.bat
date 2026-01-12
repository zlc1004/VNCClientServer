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

REM Initialize git submodules
echo Updating git submodules...
git submodule update --init --recursive
if errorlevel 1 (
    echo Failed to update git submodules!
    pause
    exit /b 1
)

REM Using explicit venv paths instead of activation

REM Install dependencies
echo Installing dependencies...
.\venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies!
    pause
    exit /b 1
)

echo Installing pyVNC library...
REM First upgrade numpy in our environment
.\venv\Scripts\pip.exe install --upgrade numpy
if errorlevel 1 (
    echo Warning: Failed to upgrade numpy
)

if exist "pyVNC\setup.py" (
    .\venv\Scripts\pip.exe install git+file:///%CD%/pyVNC
    if errorlevel 1 (
        echo Failed to install pyVNC!
        pause
        exit /b 1
    )

    echo Testing pyVNC import...
    .\venv\Scripts\python.exe -c "from pyVNC.Client import Client; print('pyVNC import test successful')" >nul 2>&1
    if errorlevel 1 (
        echo Warning: pyVNC import test failed - VNC functionality may be limited
        echo Run 'python debug_vnc_imports.py' for detailed diagnostics
        echo The application will start with QR code functionality only
    )
) else (
    echo pyVNC setup.py not found! Make sure git submodules are properly initialized.
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
