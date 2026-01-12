#!/bin/bash

echo "Starting VNC QR Server..."
echo ""

# Check if conda environment exists
if [ ! -d ".conda" ]; then
    echo "❌ Conda environment not found at ./.conda"
    echo "Please create conda environment first:"
    echo "conda create --prefix ./.conda python=3.10"
    exit 1
fi

# Use conda environment
PYTHON_PATH="./.conda/bin/python"
PIP_PATH="./.conda/bin/pip"

echo "✅ Using conda environment at ./.conda"
echo "Python version: $($PYTHON_PATH --version)"

# Git submodules no longer needed for VNC functionality
# echo "Updating git submodules..."
# git submodule update --init --recursive

# Install dependencies
echo "Installing dependencies..."
$PIP_PATH install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies!"
    exit 1
fi

echo "Checking for VNC clients..."
$PYTHON_PATH -c "
import sys
import shutil
import subprocess
import platform

print('Python version:', sys.version)
print('Platform:', platform.system())
print()

clients_found = []
system = platform.system()

if system == 'Darwin':  # macOS
    print('✅ macOS has built-in VNC support (Screen Sharing)')
    clients_found.append('Built-in Screen Sharing')
else:  # Linux
    # Check common VNC clients
    clients = ['remmina', 'vncviewer', 'vinagre', 'krdc']
    for client in clients:
        if shutil.which(client):
            clients_found.append(client)

if clients_found:
    print('✅ VNC clients found:')
    for client in clients_found:
        print(f'  - {client}')
    print()
    print('✅ VNC functionality will be available')
else:
    if system == 'Linux':
        print('❌ No VNC clients detected')
        print('VNC functionality will be limited to QR code display only')
        print()
        print('To enable VNC connections, please install one of the following:')
        print('  Ubuntu/Debian: sudo apt install remmina')
        print('  Fedora/RHEL: sudo dnf install remmina')
        print('  Or: sudo apt install tigervnc-viewer')
        print('  Or: sudo apt install vinagre')
    else:
        print('No additional VNC clients found')
print()
"

if [ $? -ne 0 ]; then
    echo "❌ Failed to check VNC clients!"
    exit 1
fi

# Start the application
echo ""
echo "🚀 Starting VNC QR Server Application..."
echo "Press Ctrl+C to stop the server"
echo ""

$PYTHON_PATH main.py
