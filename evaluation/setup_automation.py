#!/usr/bin/env python3
"""
Setup script for the automated evaluation pipeline.
Installs dependencies and validates configuration.
"""

import subprocess
import sys
import json
from pathlib import Path
import os

def install_viam_sdk():
    """Install the Viam SDK if not already installed."""
    print("🔧 Installing Viam SDK...")
    
    try:
        import viam
        print("✅ Viam SDK already installed")
        return True
    except ImportError:
        pass
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "viam-sdk"])
        print("✅ Viam SDK installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Viam SDK: {e}")
        return False

def validate_config_file(config_path):
    """Validate the Viam configuration file."""
    print(f"📋 Validating config file: {config_path}")
    
    if not Path(config_path).exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for required cloud configuration
        cloud = config.get("cloud", {})
        required_fields = ["app_address", "id", "secret"]
        
        missing_fields = [field for field in required_fields if not cloud.get(field)]
        
        if missing_fields:
            print(f"❌ Missing required cloud config fields: {missing_fields}")
            return False
        
        print("✅ Config file validation passed")
        print(f"   Machine ID: {cloud['id']}")
        print(f"   App Address: {cloud['app_address']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False

def check_viam_server():
    """Check if viam-server is available."""
    print("🔍 Checking for viam-server...")
    
    try:
        result = subprocess.run(["viam-server", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ viam-server found")
            print(f"   Version info: {result.stdout.strip()}")
            return True
        else:
            print("❌ viam-server command failed")
            return False
    except FileNotFoundError:
        print("❌ viam-server not found in PATH")
        print("💡 Please install viam-server: https://docs.viam.com/installation/")
        return False
    except subprocess.TimeoutExpired:
        print("❌ viam-server command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking viam-server: {e}")
        return False

def check_analysis_script():
    """Check if the analysis script exists."""
    script_path = Path("extract_and_align_classifier.py")
    
    if script_path.exists():
        print("✅ Analysis script found: extract_and_align_classifier.py")
        return True
    else:
        print("❌ Analysis script not found: extract_and_align_classifier.py")
        return False

def create_sample_videos_dir():
    """Create a sample videos directory structure."""
    print("📁 Setting up sample directory structure...")
    
    videos_dir = Path("../data/sample_videos")
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a sample README
    readme_path = videos_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write("""# Sample Videos Directory

Place your evaluation videos here. The automation script can process:
- Individual videos: `--videos video1.mp4 video2.mp4`
- All videos in directory: `--video-dir ../data/sample_videos`

Supported formats: .mp4, .avi, .mov, .mkv

Example video structure:
```
data/sample_videos/
├── cooking_add_remove_food.mp4
├── cooking_flip_actions.mp4
├── cooking_lid_manipulation.mp4
└── cooking_pan_operations.mp4
```

## Usage from evaluation directory:

```bash
cd evaluation/

# Process all videos in this directory
python3 automate_evaluation.py \\
    --video-dir ../data/sample_videos \\
    --output-dir ../data/results/evaluation_$(date +%Y%m%d_%H%M%S)
```
""")
    
    print(f"✅ Created sample videos directory: {videos_dir}")
    print(f"📝 See {readme_path} for usage instructions")

def create_example_usage():
    """Create an example usage script."""
    example_script = """#!/bin/bash
# Example usage of the automated evaluation pipeline

echo "🎯 Starting Automated Evaluation Pipeline"

# Option 1: Process specific videos
python3 automate_evaluation.py \\
    --videos ../data/sample_videos/video1.mp4 ../data/sample_videos/video2.mp4 \\
    --config /Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json \\
    --output-dir ../data/results/evaluation_$(date +%Y%m%d_%H%M%S) \\
    --timeout 15

# Option 2: Process all videos in a directory
# python3 automate_evaluation.py \\
#     --video-dir ../data/sample_videos \\
#     --config /Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json \\
#     --output-dir ../data/results/evaluation_$(date +%Y%m%d_%H%M%S) \\
#     --timeout 15

echo "✅ Evaluation complete!"
echo "📊 Check results in ../data/results/ directory"
"""
    
    script_path = Path("run_evaluation_example.sh")
    with open(script_path, 'w') as f:
        f.write(example_script)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"✅ Created example usage script: {script_path}")

def main():
    print("🚀 Setting up Automated Evaluation Pipeline")
    print("=" * 50)
    
    # Check and install dependencies
    success = True
    
    print("\n1. Installing dependencies...")
    if not install_viam_sdk():
        success = False
    
    print("\n2. Checking system requirements...")
    if not check_viam_server():
        success = False
    
    print("\n3. Checking analysis script...")
    if not check_analysis_script():
        success = False
    
    print("\n4. Validating configuration...")
    config_path = "/Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json"
    if not validate_config_file(config_path):
        success = False
    
    print("\n5. Checking ground truth data...")
    gt_path = "../data/datasets/ml_dataset.csv"
    if Path(gt_path).exists():
        print(f"✅ Ground truth dataset found: {gt_path}")
    else:
        print(f"⚠️  Ground truth dataset not found: {gt_path}")
        print("   This is optional - evaluation will work without it")
    
    print("\n6. Setting up directories and examples...")
    create_sample_videos_dir()
    create_example_usage()
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ Setup completed successfully!")
        print("\n🎯 Next steps:")
        print("1. Place your evaluation videos in the 'sample_videos' directory")
        print("2. Run: python3 automate_evaluation.py --help")
        print("3. Or use the example: ./run_evaluation_example.sh")
        print("\n📖 For more details, see the generated README files")
    else:
        print("❌ Setup completed with errors")
        print("Please resolve the issues above before running the automation pipeline")
    
    return success

if __name__ == "__main__":
    main() 