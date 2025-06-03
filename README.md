# Viam Camera Recording Script

Record real-time video from a Viam camera and save it as MP4. Choose between basic recording or interactive coaching mode for structured cooking action datasets with automatic timestamped action logging.

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

### 4. Test Your Connection (Recommended)

Before recording, verify your setup:

```bash
python3 test_connection.py
```

This will:

-   ✅ Check all environment variables are set
-   🔌 Test robot connection
-   📷 List available cameras
-   🖼️ Test frame capture
-   📐 Show video resolution

### 5. Configure Camera

Edit camera name in all scripts to match your Viam config:

```python
CAMERA_NAME = "your-camera-name"   # Change this in all .py files
```

### 6. Start Recording

**Option A: Use the launcher (recommended)**

```bash
python3 record.py
```

**Option B: Direct execution**

```bash
# Basic recording
python3 record_rgb.py

# Interactive coaching with action logging
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
-   **📋 Timestamped action logging**
-   Perfect for creating structured datasets
-   Output: `cooking_actions_recording.mp4` + `cooking_actions_log.csv`

#### Interactive Coaching Flow:

1. **Setup Phase**: Prepare pan, lid, and food ingredients
2. **Action Sequences** (3 repetitions each with 5-second delays):
    - Add/remove pan
    - Add/remove lid
    - Add food + perform stirring/flipping motions
    - Add/remove food from pan
3. **Free Practice**: Continue recording after guided sequence

## 📋 Action Logging & Dataset Creation

The interactive mode automatically generates timestamped logs perfect for machine learning:

### **Generated Files:**

-   🎥 **Video**: `cooking_actions_recording.mp4` - The actual recording
-   📊 **Action Log**: `cooking_actions_log.csv` - Timestamped action labels

### **CSV Format:**

```csv
session_timestamp,action_category,action_description,repetition_number,start_time_seconds,end_time_seconds,duration_seconds,video_filename,notes
2024-06-03 14:30:15,pan_manipulation,"Add the pan to the cooking area, then remove it",1,15.23,18.45,3.22,cooking_actions_recording.mp4,"Repetition 1 of 3"
2024-06-03 14:30:23,pan_manipulation,"Add the pan to the cooking area, then remove it",2,23.67,26.89,3.22,cooking_actions_recording.mp4,"Repetition 2 of 3"
```

### **Action Categories:**

-   🍳 **`pan_manipulation`** - Adding/removing pan
-   🎯 **`lid_manipulation`** - Adding/removing lid
-   🥄 **`food_cooking`** - Stirring/flipping food
-   🍎 **`food_manipulation`** - Adding/removing food
-   📊 **`phase_transition`** - Session phases (setup, coaching, free practice)

### **Analyze Your Data:**

```bash
python3 analyze_log.py
```

**Analysis Features:**

-   📊 Action statistics and timing analysis
-   📈 Timeline visualization (requires matplotlib)
-   🤖 ML-ready dataset export
-   ⚖️ Dataset balance checking

**Example Output:**

```
📊 Analyzing action log: cooking_actions_log.csv
🥄 Cooking Actions Analysis:
   Total actions: 12
   Action categories: 4
   Average duration: 3.2s
   Total action time: 38.4s

📊 Action Categories:
   pan_manipulation: 3 actions, avg 3.2s, total 9.6s
   lid_manipulation: 3 actions, avg 2.8s, total 8.4s
   food_cooking: 3 actions, avg 4.1s, total 12.3s
   food_manipulation: 3 actions, avg 2.7s, total 8.1s

🤖 Machine Learning Dataset Summary:
   Video segments: 12 labeled actions
   Classes: ['pan_manipulation', 'lid_manipulation', 'food_cooking', 'food_manipulation']
   Balanced dataset: Yes
```

## 🔍 Connection Logging & Debugging

Both recording scripts now provide detailed logging:

### Connection Status

```
🔌 Attempting to connect to Viam robot...
   Address: my-machine.viam.cloud:8080
   API Key ID: ck_1234567890abcdef...
✅ Successfully connected to Viam robot!
📋 Robot status retrieved - 5 resources found
```

### Camera Connection

```
📷 Attempting to connect to camera: 'overhead-rgb'
✅ Successfully connected to camera!
🖼️  Getting first frame to determine video resolution...
📐 Video resolution detected: 1280x720
```

### Recording Progress

```
🎥 Recording started!
   Camera: overhead-rgb
   Output: overhead_rgb_live.mp4
   Resolution: 1280x720
   FPS: 10
📹 Recording... (Press Ctrl-C to stop)
📊 Recorded 1000 frames (100.0 seconds)
```

### Action Logging (Interactive Mode)

```
📋 Action log will be saved to: cooking_actions_log.csv
📝 Logging action start: Add the pan to the cooking area, then remove it (Rep 1) at 15.2s
✅ Action logged: 3.2s duration
```

### Error Handling

-   ❌ Clear error messages for common issues
-   ⚠️ Warnings for non-critical problems
-   🔧 Suggested fixes for connection problems

## 📁 Files

-   `record.py` - **Main launcher script**
-   `record_rgb.py` - Basic recording script
-   `record_rgb_interactive.py` - **Interactive coaching script with action logging**
-   `analyze_log.py` - **Action log analysis and visualization tool**
-   `test_connection.py` - **Connection verification tool**
-   `requirements.txt` - Python dependencies
-   `setup_environment.sh` - Environment setup script
-   `README.md` - This file

## ⚙️ Configuration Options

Edit these variables in the recording scripts:

```python
CAMERA_NAME = "overhead-rgb"   # Your camera name from Viam config
FPS         = 10               # Frames per second for recording
OUT_FILE    = "video_name.mp4" # Output filename
LOG_FILE    = "actions_log.csv" # Action log filename (interactive mode)
```

## 🍳 Interactive Coaching Features

The interactive mode provides:

-   **📋 Pre-recording checklist** - Ensures proper setup
-   **🎯 Action queuing** - Step-by-step guidance
-   **⏱️ Automatic timing** - 5-second delays between repetitions
-   **🔄 Repetition tracking** - 3 repetitions per action type
-   **🥄 Cooking method detection** - Adapts to stirring vs. flipping
-   **✅ Progress feedback** - Clear completion indicators
-   **📊 Action logging** - Automatic timestamped labels

Perfect for creating consistent training datasets for:

-   Object manipulation research
-   Cooking action recognition
-   Robotic learning applications
-   Human-robot interaction studies

## 🤖 Machine Learning Ready

### **Automatic Dataset Generation:**

Each interactive session creates:

1. **Labeled video segments** with precise timing
2. **Balanced action classes** (3 reps per action type)
3. **Consistent action structure** across sessions
4. **CSV annotations** ready for ML pipelines

### **Use Cases:**

-   **Action Recognition**: Train models to classify cooking actions
-   **Temporal Segmentation**: Detect action boundaries in video
-   **Imitation Learning**: Robot learning from human demonstrations
-   **Behavior Analysis**: Study human cooking patterns

### **Integration Example:**

```python
import pandas as pd
import cv2

# Load action annotations
actions = pd.read_csv('cooking_actions_log.csv')
video = cv2.VideoCapture('cooking_actions_recording.mp4')

# Extract action segments for training
for _, action in actions.iterrows():
    start_frame = int(action['start_time_seconds'] * 10)  # 10 FPS
    end_frame = int(action['end_time_seconds'] * 10)
    label = action['action_category']
    # Process video segment...
```

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
2. **Logging Init**: Creates CSV file with headers
3. **Coaching**: Runs action sequences with confirmations
4. **Timestamping**: Logs start/end times for each action
5. **Recording**: Captures video concurrently with coaching
6. **Analysis**: Processes logs for ML-ready datasets

## 📋 Prerequisites

-   Python ≥ 3.9
-   pip ≥ 23
-   Active Viam robot with camera configured
-   Internet connection for cloud access

## 🆘 Troubleshooting

### Quick Diagnosis

Run the connection test first:

```bash
python3 test_connection.py
```

### "Camera not found"

-   Check your `CAMERA_NAME` matches exactly what's in your Viam config
-   Verify your robot is online at app.viam.com
-   Run `test_connection.py` to see available cameras

### "Authentication failed"

-   Double-check your API key and machine address
-   Make sure environment variables are set in the same terminal session
-   Verify your API key has the right permissions at app.viam.com

### "Module not found"

-   Ensure virtual environment is activated: `source venv/bin/activate`
-   Try reinstalling: `pip install -r requirements.txt`

### Interactive mode not responding

-   Make sure you're pressing ENTER after each prompt
-   Check that your terminal supports interactive input
-   Try running `python3 record_rgb_interactive.py` directly

### Connection timeouts

-   Check your internet connection
-   Verify robot is online and accessible
-   Try restarting your robot if issues persist

### Analysis script issues

-   Install analysis dependencies: `pip install pandas matplotlib`
-   Check that CSV file exists: `ls -la cooking_actions_log.csv`
-   Run with custom file: `python3 analyze_log.py your_log.csv`

## 📊 Use Cases

### Research Applications

-   **Computer Vision**: Object detection and tracking datasets
-   **Robotics**: Imitation learning and action recognition
-   **HCI Studies**: Human behavior analysis during cooking tasks

### Data Collection

-   **Consistent Actions**: Guided sequences ensure uniform data
-   **Temporal Structure**: Built-in timing for action boundaries
-   **Multi-Modal**: Combine with other sensors for rich datasets
-   **Automatic Labeling**: No manual annotation required

### Machine Learning

-   **Supervised Learning**: Pre-labeled action classification
-   **Temporal Models**: Sequence modeling and prediction
-   **Transfer Learning**: Pre-trained on cooking actions
-   **Evaluation**: Standardized test datasets

## 📄 License

This project follows the MIT License pattern for open-source development.
