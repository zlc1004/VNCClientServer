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

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements if they don't exist
if not exist "venv\Lib\site-packages\flask\" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )

    echo Installing pyVNC library...
    if exist "pyVNC\setup.py" (
        pip install git+file:///%CD%/pyVNC
        if errorlevel 1 (
            echo Failed to install pyVNC!
            pause
            exit /b 1
        )
    ) else (
        echo pyVNC setup.py not found! Make sure git submodules are properly initialized.
        pause
        exit /b 1
    )
)

REM Start the application
echo.
echo Starting VNC QR Server Application...
echo Press Ctrl+C to stop the server
echo.
python main.py

pause
