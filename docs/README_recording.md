# 📹 Recording Tools

This directory contains all tools for recording cooking actions using Viam cameras.

## 🛠️ Available Scripts

### `record.py`

**Simple recording launcher**

-   Basic entry point for recording functionality
-   Provides menu-driven interface for recording options

### `record_rgb.py`

**Basic RGB camera recording**

-   Connects to Viam camera and records MP4 video
-   Real-time display with frame counter overlay
-   Configurable FPS and output settings

**Usage:**

```bash
cd recording/
VIAM_CAMERA_NAME="overhead-rgb" python3 record_rgb.py
```

### `record_rgb_interactive.py`

**Interactive cooking action recording**

-   Guided recording session for specific cooking actions
-   Records separate video files for each action type
-   Built-in cooking coach with action prompts
-   Automatic action logging and timeline generation

**Features:**

-   Step-by-step cooking guidance
-   Separate videos per action (add-pan, remove-food, etc.)
-   Automatic CSV logging of actions and timestamps
-   Real-time feedback and coaching

**Usage:**

```bash
cd recording/
VIAM_CAMERA_NAME="overhead-rgb" python3 record_rgb_interactive.py
```

### `test_connection.py`

**Viam connection testing**

-   Tests connectivity to Viam robot and cameras
-   Validates camera functionality
-   Useful for troubleshooting setup issues

### `setup_environment.sh`

**Environment setup script**

-   Sets up recording environment
-   Installs required dependencies
-   Configures environment variables

## 🔧 Setup

1. **Install dependencies:**

    ```bash
    pip install -r ../requirements.txt
    ```

2. **Set environment variables:**

    ```bash
    export VIAM_CAMERA_NAME="your_camera_name"
    ```

3. **Test connection:**
    ```bash
    cd recording/
    python3 test_connection.py
    ```

## 📁 Output Files

Recording scripts generate:

-   **Video files:** `cooking_actions_*.mp4`
-   **Action logs:** `cooking_actions_log.csv`
-   **Timeline data:** For analysis and evaluation

## 🎯 Workflow

```
1. Setup Environment → 2. Test Connection → 3. Interactive Recording → 4. Review Outputs
```

## 🔗 Integration

Recorded videos can be used with the [evaluation tools](../evaluation/) for:

-   Action classification analysis
-   Performance evaluation
-   Model training data generation

## 📋 Requirements

-   Viam robot with configured camera
-   Python 3.7+
-   OpenCV
-   Viam SDK
-   Valid Viam machine configuration
