#!/bin/bash
# Example usage of the automated evaluation pipeline

echo "🎯 Starting Automated Evaluation Pipeline"

# Option 1: Process specific videos
python3 automate_evaluation.py \
    --videos ../data/sample_videos/video1.mp4 ../data/sample_videos/video2.mp4 \
    --config /Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json \
    --output-dir ../data/results/evaluation_$(date +%Y%m%d_%H%M%S) \
    --timeout 15

# Option 2: Process all videos in a directory
# python3 automate_evaluation.py \
#     --video-dir ../data/sample_videos \
#     --config /Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json \
#     --output-dir ../data/results/evaluation_$(date +%Y%m%d_%H%M%S) \
#     --timeout 15

echo "✅ Evaluation complete!"
echo "📊 Check results in ../data/results/ directory"
