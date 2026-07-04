#!/bin/bash
# Build script for macOS
# Run this on a macOS machine with Python 3.8+ installed

set -e

echo "=== Building Pinchu for macOS ==="

# Check Python version
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Clean previous builds
rm -rf build dist Pinchu.app

# Build with PyInstaller
echo "Building Pinchu.app..."
pyinstaller \
    --name Pinchu \
    --onedir \
    --windowed \
    --icon=NONE \
    --add-data "ui:ui" \
    --add-data "config.py:." \
    --add-data "activity_monitor.py:." \
    --add-data "ai_client.py:." \
    --add-data "voice.py:." \
    --add-data "memory.py:." \
    --add-data "task_manager.py:." \
    --add-data "overlay.py:." \
    --add-data "tray.py:." \
    --add-data "context_chain.py:." \
    --add-data "cli.py:." \
    --clean \
    --noconfirm \
    main.py

echo "Build complete!"
echo "Output: dist/Pinchu/Pinchu.app"

# Create zip
echo "Creating Pinchu-macOS.zip..."
cd dist
ditto -c -k --sequesterRsrc --keepParent Pinchu Pinchu-macOS.zip
echo "Zip created: dist/Pinchu-macOS.zip"

echo ""
echo "=== Build Complete ==="
echo "Your macOS build is at: dist/Pinchu/Pinchu.app"
echo "Zip file: dist/Pinchu-macOS.zip"
echo ""
echo "To distribute:"
echo "1. Upload Pinchu-macOS.zip to GitHub Release"
echo "2. Users can extract and run Pinchu.app"
