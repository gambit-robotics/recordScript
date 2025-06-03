#!/bin/bash

echo "🚀 Setting up Viam Camera Recording Environment"
echo "=============================================="

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📋 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Set up your .env file with your Viam credentials:"
echo "   VIAM_API_KEY_ID=your_api_key_id"
echo "   VIAM_API_KEY=your_api_key"
echo "   VIAM_ADDRESS=your_machine_address:8080"
echo "   VIAM_CAMERA_NAME=your_camera_name"
echo "3. Test your connection: python3 test_connection.py"
echo "4. Start recording: python3 record.py"
echo ""
echo "Press Ctrl-C to stop recording." 