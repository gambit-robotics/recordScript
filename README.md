# Viam Camera Recording Script

Record real-time video from a Viam camera and save it as MP4. Choose between basic recording or interactive coaching mode for structured cooking action datasets.

## 🚀 Quick Start

### 1. Setup Environment

```bash
chmod +x setup_environment.sh
./setup_environment.sh
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Configure Credentials

Get your credentials from [app.viam.com](https://app.viam.com):

-   Go to **API Keys** → **"Create key…"**
-   Go to **Connect** → **Code Sample** for your machine's address

```bash
export VIAM_API_KEY_ID="ck_************************"
export VIAM_API_KEY="vs_************************"
export VIAM_ADDRESS="your-machine.viam.cloud:8080"
```

### 4. Configure Camera

Edit camera name in `record_rgb.py` and `record_rgb_interactive.py`:

```python
CAMERA_NAME = "your-camera-name"   # Change this to match your Viam config
```

### 5. Start Recording

**Option A: Use the launcher (recommended)**

```bash
python3 record.py
```

**Option B: Direct execution**

```bash
# Basic recording
python3 record_rgb.py

# Interactive coaching
python3 record_rgb_interactive.py
```

Press **Ctrl-C** to stop recording.

## 🎯 Recording Modes

### 1. Basic Recording (`record_rgb.py`)

-   Simple continuous video capture
-   Manual start/stop with Ctrl-C
-   Output: `overhead_rgb_live.mp4`

### 2. Interactive Coaching (`record_rgb_interactive.py`)

-   **Guided cooking action sequences**
-   **Step-by-step prompts with confirmations**
-   **Automatic timing between actions**
-   Perfect for creating structured datasets
-   Output: `cooking_actions_recording.mp4`

#### Interactive Coaching Flow:

1. **Setup Phase**: Prepare pan, lid, and food ingredients
2. **Action Sequences** (3 repetitions each with 5-second delays):
    - Add/remove pan
    - Add/remove lid
    - Add food + perform stirring/flipping motions
    - Add/remove food from pan
3. **Free Practice**: Continue recording after guided sequence

## 📁 Files

-   `record.py` - **Main launcher script**
-   `record_rgb.py` - Basic recording script
-   `record_rgb_interactive.py` - **Interactive coaching script**
-   `requirements.txt` - Python dependencies
-   `setup_environment.sh` - Environment setup script
-   `README.md` - This file

## ⚙️ Configuration Options

Edit these variables in the recording scripts:

```python
CAMERA_NAME = "overhead-rgb"   # Your camera name from Viam config
FPS         = 10               # Frames per second for recording
OUT_FILE    = "video_name.mp4" # Output filename
```

## 🍳 Interactive Coaching Features

The interactive mode provides:

-   **📋 Pre-recording checklist** - Ensures proper setup
-   **🎯 Action queuing** - Step-by-step guidance
-   **⏱️ Automatic timing** - 5-second delays between repetitions
-   **🔄 Repetition tracking** - 3 repetitions per action type
-   **🥄 Cooking method detection** - Adapts to stirring vs. flipping
-   **✅ Progress feedback** - Clear completion indicators

Perfect for creating consistent training datasets for:

-   Object manipulation research
-   Cooking action recognition
-   Robotic learning applications
-   Human-robot interaction studies

## 🔧 Advanced Options

### Smaller File Size

Convert to smaller file with better compression:

```bash
ffmpeg -i cooking_actions_recording.mp4 -c:v libx264 -crf 24 smaller.mp4
```

### Lossless Master Recording

For highest quality, change in recording scripts:

```python
fourcc = cv2.VideoWriter_fourcc(*"ffv1")  # Lossless codec
OUT_FILE = "recording.mkv"                # Use .mkv extension
```

### Custom Action Sequences

Modify the `actions` list in `record_rgb_interactive.py`:

```python
actions = [
    ("Your custom action description", 3),  # 3 repetitions
    ("Another action", 5),                  # 5 repetitions
]
```

### Multi-Camera Setup

Create multiple `Camera.from_robot()` instances and separate files for each camera.

## 🛠️ How It Works

### Basic Recording

1. **Connect**: Uses Viam SDK with API key authentication
2. **Capture**: Streams JPEG frames via `Camera.get_image()`
3. **Process**: Decodes JPEG to NumPy arrays with OpenCV
4. **Record**: Writes frames to MP4 using `cv2.VideoWriter`
5. **Cleanup**: Graceful shutdown on Ctrl-C

### Interactive Coaching

1. **Setup**: Guides user through preparation checklist
2. **Coaching**: Runs action sequences with confirmations
3. **Recording**: Captures video concurrently with coaching
4. **Timing**: Enforces delays between action repetitions
5. **Completion**: Allows free practice after guided sequence

## 📋 Prerequisites

-   Python ≥ 3.9
-   pip ≥ 23
-   Active Viam robot with camera configured
-   Internet connection for cloud access

## 🆘 Troubleshooting

### "Camera not found"

-   Check your `CAMERA_NAME` matches exactly what's in your Viam config
-   Verify your robot is online at app.viam.com

### "Authentication failed"

-   Double-check your API key and machine address
-   Make sure environment variables are set in the same terminal session

### "Module not found"

-   Ensure virtual environment is activated: `source venv/bin/activate`
-   Try reinstalling: `pip install -r requirements.txt`

### Interactive mode not responding

-   Make sure you're pressing ENTER after each prompt
-   Check that your terminal supports interactive input
-   Try running `python3 record_rgb_interactive.py` directly

## 📊 Use Cases

### Research Applications

-   **Computer Vision**: Object detection and tracking datasets
-   **Robotics**: Imitation learning and action recognition
-   **HCI Studies**: Human behavior analysis during cooking tasks

### Data Collection

-   **Consistent Actions**: Guided sequences ensure uniform data
-   **Temporal Structure**: Built-in timing for action boundaries
-   **Multi-Modal**: Combine with other sensors for rich datasets

## 📄 License

This project follows the MIT License pattern for open-source development.
