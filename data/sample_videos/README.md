# Sample Videos Directory

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
python3 automate_evaluation.py \
    --video-dir ../data/sample_videos \
    --output-dir ../data/results/evaluation_$(date +%Y%m%d_%H%M%S)
```
