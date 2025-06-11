# 🔍 Evaluation Tools

This directory contains automated tools for evaluating action classification performance against recorded videos.

## 🚀 Main Tools

### `automate_evaluation.py`

**🎯 Fully Automated Evaluation Pipeline**

The crown jewel of the evaluation suite - completely automates your entire evaluation workflow!

**What it does:**

1. **Updates Viam machine config** via cloud API with new video paths
2. **Runs viam-server** and captures all logs in real-time
3. **Detects video completion** automatically (`"End of file => stopping playback"`)
4. **Runs analysis** immediately using `extract_and_align_classifier.py`
5. **Repeats for all videos** without manual intervention
6. **Generates comprehensive reports** with cross-video metrics

**Usage:**

```bash
cd evaluation/

# Process specific videos
python3 automate_evaluation.py \
    --videos /path/to/video1.mp4 /path/to/video2.mp4 /path/to/video3.mp4 \
    --output-dir results_$(date +%Y%m%d_%H%M%S) \
    --timeout 15

# Process all videos in a directory
python3 automate_evaluation.py \
    --video-dir /Users/marcuslam/Desktop/Gambit_data/marcus_eval_video \
    --output-dir results_$(date +%Y%m%d_%H%M%S) \
    --timeout 15
```

**Key Features:**

-   ✅ **Zero manual intervention** - set it and forget it!
-   ✅ **Smart end detection** - knows when videos finish
-   ✅ **Cloud config updates** - uses Viam API properly
-   ✅ **Automatic analysis** - immediate processing of logs
-   ✅ **Cross-video insights** - aggregate performance metrics
-   ✅ **Safe restoration** - restores original config when done

### `extract_and_align_classifier.py`

**📊 Log Analysis & Performance Evaluation**

Parses viam-server logs and extracts action classification results with detailed performance analysis.

**Features:**

-   Extracts classifier detections with confidence scores
-   Aligns with ground truth data (`../data/datasets/ml_dataset.csv`)
-   Calculates recall, precision, and coverage metrics
-   Provides actionable insights and recommendations
-   Exports detailed timelines and summaries

**Usage:**

```bash
cd evaluation/
python3 extract_and_align_classifier.py /path/to/logs.txt
```

### `analyze_log.py`

**📈 Legacy Log Analyzer**

Legacy tool for parsing older log formats and generating ML datasets.

### `setup_automation.py`

**⚙️ Setup & Validation**

Installs dependencies and validates your evaluation environment.

**What it checks:**

-   Viam SDK installation
-   viam-server availability
-   Configuration file validity
-   Analysis script presence

**Usage:**

```bash
cd evaluation/
python3 setup_automation.py
```

## 🎯 Quick Start

### 1. Setup (One-time)

```bash
cd evaluation/
python3 setup_automation.py
```

### 2. Run Automated Evaluation

```bash
# Put your videos in the data directory
mkdir -p ../data/evaluation_videos/
cp /path/to/your/videos/*.mp4 ../data/evaluation_videos/

# Run automation
python3 automate_evaluation.py \
    --video-dir ../data/evaluation_videos \
    --output-dir ../data/results/evaluation_$(date +%Y%m%d_%H%M%S) \
    --timeout 15
```

### 3. Review Results

```bash
# Results are saved to specified output directory:
ls ../data/results/evaluation_20250611_120000/
# ├── video1_20250611_120001.log           # Raw logs
# ├── video1_20250611_120001.analysis.txt  # Detailed analysis
# ├── video2_20250611_120035.log
# ├── video2_20250611_120035.analysis.txt
# └── evaluation_results_20250611_120000.json  # Summary report
```

## 📊 What You Get

### Per-Video Analysis

-   **Action detections** with confidence scores
-   **Motion similarity** analysis
-   **Analysis timing** performance
-   **Acceptance/rejection** breakdown
-   **Detailed timeline** of all events

### Cross-Video Summary

-   **Overall detection rates** across all videos
-   **Average confidence** and performance metrics
-   **Coverage analysis** vs ground truth data
-   **Performance recommendations** for optimization
-   **Aggregate statistics** and trends

## 🔄 Migration from Manual Process

**Before (Manual):**

```bash
# 1. Manually edit Viam config file with video path
# 2. Run: viam-server -config /path/to/config.json
# 3. Wait for video to finish, copy logs to file
# 4. Run: python3 extract_and_align_classifier.py logs.txt
# 5. Repeat for each video... 😴
```

**After (Automated):**

```bash
# Just one command!
python3 automate_evaluation.py --video-dir /path/to/videos
# ☕ Grab coffee while it processes all videos automatically!
```

## 🛠️ Configuration

The automation uses your existing Viam configuration:

-   **Cloud config:** `/Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json`
-   **Machine ID:** `de6836af-05f6-4ff4-a067-8d18ac0f6495`
-   **Target component:** `replayCamera-1` (video replay camera)

## 🔗 Integration

Works seamlessly with:

-   **[Recording tools](../recording/)** - Use recorded videos for evaluation
-   **[Ground truth data](../data/datasets/)** - Compares against labeled datasets
-   **Viam cloud platform** - Updates machine configs via API

## 📋 Requirements

-   Python 3.7+
-   Viam SDK (`pip install viam-sdk`)
-   Valid Viam machine configuration
-   viam-server installed and in PATH

## 🚨 Troubleshooting

**Common issues:**

-   **"Machine ID not found"** → Check your config file has correct cloud credentials
-   **"viam-server not found"** → Install viam-server and add to PATH
-   **"Config update failed"** → Verify your Viam API credentials are valid
-   **"Analysis failed"** → Check `extract_and_align_classifier.py` is in same directory

**Debug mode:**

```bash
# Run with verbose output for debugging
python3 automate_evaluation.py --video-dir /path/to/videos --timeout 30
```
