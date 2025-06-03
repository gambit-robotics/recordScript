#!/bin/bash

echo "Setting up Viam Camera Recording Environment"
echo "=============================================="

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set your Viam credentials (get these from app.viam.com):"
echo "   export VIAM_API_KEY_ID=\"ck_************************\""
echo "   export VIAM_API_KEY=\"vs_************************\""
echo "   export VIAM_ADDRESS=\"your-machine.viam.cloud:8080\""
echo "3. Edit CAMERA_NAME in record_rgb.py to match your Viam config"
echo "4. Run: python3 record_rgb.py"
echo ""
echo "Press Ctrl-C to stop recording." 