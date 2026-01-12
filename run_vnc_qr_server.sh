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

# Initialize git submodules
echo "Updating git submodules..."
git submodule update --init --recursive
if [ $? -ne 0 ]; then
    echo "❌ Failed to update git submodules!"
    exit 1
fi

# Check if requirements are installed
if [ ! -f ".conda/.deps_installed" ]; then
    echo "Installing dependencies..."
    $PIP_PATH install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies!"
        exit 1
    fi

    echo "Installing pyVNC library..."
    $PIP_PATH install -e ./pyVNC/
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install pyVNC!"
        exit 1
    fi

    touch .conda/.deps_installed
fi

# Start the application
echo ""
echo "🚀 Starting VNC QR Server Application..."
echo "Press Ctrl+C to stop the server"
echo ""

$PYTHON_PATH main.py
