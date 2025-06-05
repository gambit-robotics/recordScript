# Viam Camera Recording Script

Record real-time video from a Viam camera and save it as MP4. Choose between basic recording or interactive coaching mode for structured cooking action datasets with automatic timestamped action logging and live video preview.

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

**create a `.env` file:**

```bash
VIAM_API_KEY_ID=************************
VIAM_API_KEY=************************
VIAM_ADDRESS=your-machine.viam.cloud
VIAM_CAMERA_NAME=your-camera-name
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

### 5. Start Recording

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

Press **Ctrl-C** to stop recording or **'q'** in the live feed window.

## 🎯 Recording Modes

### 1. Basic Recording (`record_rgb.py`)

-   Simple continuous video capture
-   Manual start/stop with Ctrl-C
-   **📺 Live video preview window** ← NEW!
-   Output: `overhead_rgb_live.mp4`

### 2. Interactive Coaching (`record_rgb_interactive.py`)

-   **Guided cooking action sequences**
-   **Step-by-step prompts with confirmations**
-   **Automatic timing between actions**
-   **📋 Timestamped action logging**
-   **📺 Live feed with coaching overlays** ← NEW!
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

## 📺 Live Video Feed

Both recording modes now display real-time video with helpful overlays:

### **Basic Recording Features:**

-   🔴 **Recording indicator** - Red circle and "REC" text
-   📊 **Frame counter** - Shows current frame and recording time
-   ⌨️ **Keyboard control** - Press 'q' to stop recording
-   🖼️ **Auto-sizing window** - Adapts to camera resolution

### **Interactive Mode Features:**

-   🎯 **Current action display** - Shows what action you should be doing
-   📝 **Action progress** - "Add pan (Rep 2/3)" format
-   ⏱️ **Wait indicators** - "Waiting... (Next: Rep 3/3)"
-   🎉 **Phase updates** - "Free practice - do anything!"
-   📊 **Recording stats** - Frame count and duration

### **Live Feed Controls:**

```python
SHOW_LIVE_FEED = True   # Set to False for headless recording
```

**Control Options:**

-   **'q' key** - Stop recording and close window
-   **Ctrl-C** - Stop recording (terminal)
-   **Window close button** - Stop recording

### **Display Examples:**

**Basic Recording:**

```
┌─────────────────────────────┐
│ 🔴 REC                      │
│                             │
│     [Live Camera Feed]      │
│                             │
│ Frame: 1234 | Time: 123.4s  │
│                Press 'q'     │
└─────────────────────────────┘
```

**Interactive Coaching:**

```
┌─────────────────────────────┐
│    Add pan (Rep 2/3)        │
│ 🔴 REC                      │
│                             │
│     [Live Camera Feed]      │
│                             │
│ Frame: 1234 | Time: 123.4s  │
│                Press 'q'     │
└─────────────────────────────┘
```

## 📋 Action Logging & Dataset Creation

The interactive mode automatically generates timestamped logs perfect for machine learning:

### **Generated Files:**

-   🎥 **Video**: `cooking_actions_recording.mp4` - The actual recording
-   📊 **Action Log**: `cooking_actions_log.csv` - Timestamped action labels

### **CSV Format:**

```csv
session_timestamp,action_category,action_description,repetition_number,start_time_seconds,end_time_seconds,duration_seconds,video_filename,notes
2024-06-03 14:30:15,pan_manipulation,add-pan,1,15.23,18.45,3.22,cooking_actions_recording.mp4,"add-pan completed"
2024-06-03 14:30:23,pan_manipulation,remove-pan,1,23.67,26.89,3.22,cooking_actions_recording.mp4,"remove-pan completed"
2024-06-03 14:30:35,lid_manipulation,add-lid,1,35.45,38.67,3.22,cooking_actions_recording.mp4,"add-lid completed"
2024-06-03 14:30:47,food_manipulation,add-food,1,47.89,51.11,3.22,cooking_actions_recording.mp4,"add-food completed"
2024-06-03 14:30:59,food_cooking,stir,1,59.33,62.55,3.22,cooking_actions_recording.mp4,"stir completed"
```

### **Action Descriptions:**

**Simple, standardized labels perfect for ML:**

-   🍳 **`add-pan`**, **`remove-pan`** - Pan manipulation
-   🎯 **`add-lid`**, **`remove-lid`** - Lid manipulation
-   🥄 **`stir`**, **`flip`** - Cooking motions
-   🍎 **`add-food`**, **`remove-food`** - Food manipulation
-   🧂 **`season`** - Seasoning actions

### **Action Categories:**

-   🍳 **`pan_manipulation`** - add-pan, remove-pan
-   🎯 **`lid_manipulation`** - add-lid, remove-lid
-   🥄 **`food_cooking`** - stir, flip
-   🍎 **`food_manipulation`** - add-food, remove-food
-   🧂 **`food_seasoning`** - season
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
   Address: my-machine.viam.cloud
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
   Live feed: Enabled
📺 Live feed window opened. Press 'q' in the video window or Ctrl-C to stop.
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
-   `record_rgb.py` - Basic recording script with live feed
-   `record_rgb_interactive.py` - **Interactive coaching script with action logging and live feed**
-   `analyze_log.py` - **Action log analysis and visualization tool**
-   `test_connection.py` - **Connection verification tool**
-   `requirements.txt` - Python dependencies
-   `setup_environment.sh` - Environment setup script
-   `README.md` - This file

## ⚙️ Configuration Options

All configuration is now handled via environment variables and `.env` file:

```bash
# Environment Variables (.env file)
VIAM_API_KEY_ID=your_api_key_id
VIAM_API_KEY=your_api_key
VIAM_ADDRESS=your_machine_address
VIAM_CAMERA_NAME=your_camera_name
```

**Optional settings** you can edit in the recording scripts:

```python
FPS         = 10               # Frames per second for recording
OUT_FILE    = "video_name.mp4" # Output filename
LOG_FILE    = "actions_log.csv" # Action log filename (interactive mode)
SHOW_LIVE_FEED = True          # Display live video window
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
-   **📺 Live video coaching** - Real-time visual feedback ← NEW!

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

# Load ML-ready dataset (exported by analyze_log.py)
ml_data = pd.read_csv('ml_dataset.csv')
video = cv2.VideoCapture('cooking_actions_recording.mp4')

# The ML dataset includes both category and precise action labels
print("Available columns:", ml_data.columns.tolist())
# ['video_filename', 'category_label', 'action_label', 'start_time_seconds',
#  'end_time_seconds', 'duration_seconds', 'video_start_frame', 'video_end_frame']

# Extract action segments for training
for _, segment in ml_data.iterrows():
    start_frame = segment['video_start_frame']
    end_frame = segment['video_end_frame']

    category = segment['category_label']      # e.g., 'food_cooking'
    action = segment['action_label']          # e.g., 'stir'

    # Use either broad categories or precise actions for training
    label = action  # Use precise action labels for fine-grained classification
    # label = category  # Or use broader categories for coarse classification

    # Extract video frames
    video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frames = []
    for frame_num in range(start_frame, end_frame):
        ret, frame = video.read()
        if ret:
            frames.append(frame)

    # Process frames for your model...
    print(f"Segment: {action} ({category}) - {len(frames)} frames")
```

**Generated ML Dataset Format:**

```csv
video_filename,category_label,action_label,start_time_seconds,end_time_seconds,duration_seconds,video_start_frame,video_end_frame
cooking_actions_recording.mp4,pan_manipulation,add-pan,15.23,18.45,3.22,152,184
cooking_actions_recording.mp4,pan_manipulation,remove-pan,23.67,26.89,3.22,236,268
cooking_actions_recording.mp4,food_cooking,stir,59.33,62.55,3.22,593,625
```

## 🔧 Advanced Options

### Disable Live Feed (Headless Mode)

For servers or automated recording:

```python
SHOW_LIVE_FEED = False
```

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
4. **Display**: Shows live feed with recording overlays
5. **Record**: Writes frames to MP4 using `cv2.VideoWriter`
6. **Cleanup**: Graceful shutdown on Ctrl-C or 'q' key

### Interactive Coaching

1. **Setup**: Guides user through preparation checklist
2. **Logging Init**: Creates CSV file with headers
3. **Coaching**: Runs action sequences with confirmations
4. **Timestamping**: Logs start/end times for each action
5. **Recording**: Captures video concurrently with coaching
6. **Live Display**: Shows current action status in video overlay
7. **Analysis**: Processes logs for ML-ready datasets

## 📋 Prerequisites

-   Python ≥ 3.9
-   pip ≥ 23
-   Active Viam robot with camera configured
-   Internet connection for cloud access
-   **Display/GUI environment** (for live feed - use `SHOW_LIVE_FEED = False` for headless)

## 🆘 Troubleshooting

### Quick Diagnosis

Run the connection test first:

```bash
python3 test_connection.py
```

### "Camera not found"

-   Check your `VIAM_CAMERA_NAME` environment variable matches exactly what's in your Viam config
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

### Live feed issues

-   **No display environment**: Set `SHOW_LIVE_FEED = False` for headless operation
-   **Window doesn't appear**: Check your system supports OpenCV GUI (install `opencv-python` not `opencv-python-headless`)
-   **Performance issues**: Lower FPS or disable live feed for better recording performance

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
-   **Visual Verification**: Live feed ensures quality data collection

### Machine Learning

-   **Supervised Learning**: Pre-labeled action classification
-   **Temporal Models**: Sequence modeling and prediction
-   **Transfer Learning**: Pre-trained on cooking actions
-   **Evaluation**: Standardized test datasets

## 📄 License

This project follows the MIT License pattern for open-source development.
