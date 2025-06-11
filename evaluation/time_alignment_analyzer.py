#!/usr/bin/env python3
"""
Time Alignment Analyzer for Detection Timeline vs Ground Truth

This script aligns classifier detections (HH:MM:SS timestamps) with ground truth
action labels (seconds from video start) to evaluate detection accuracy with
temporal tolerance.

Usage:
    python time_alignment_analyzer.py [detection_log] [ground_truth_csv] [video_start_time] [tolerance_seconds] [--no-stretch]
"""

import pandas as pd
import re
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

class TimeAlignmentAnalyzer:
    def __init__(self, tolerance_seconds=10.0, stretch_timeline=True):
        """
        Initialize the analyzer with temporal tolerance.
        
        Args:
            tolerance_seconds: How many seconds +/- to consider a match
            stretch_timeline: Whether to stretch GT timeline to match detection span
        """
        self.tolerance = tolerance_seconds
        self.stretch_timeline = stretch_timeline
        self.detections = []
        self.ground_truth = []
        self.video_start_time = None
        self.stretch_factor = 1.0
        
    def load_detections_from_log(self, log_file):
        """Load detections from classification timeline log."""
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Extract detections using regex pattern for the timeline format
        pattern = r'# Detection \d+ - (\d{2}:\d{2}:\d{2}) - ([^#\n]+)'
        matches = re.findall(pattern, content)
        
        detections = []
        for time_str, action in matches:
            detections.append({
                'time_hms': time_str,
                'action': action.strip(),
                'time_seconds': None  # Will be calculated after setting video start time
            })
        
        self.detections = detections
        print(f"📊 Loaded {len(detections)} detections from log")
        return detections
    
    def load_ground_truth_from_csv(self, csv_file):
        """Load ground truth from ML dataset CSV."""
        df = pd.read_csv(csv_file)
        
        ground_truth = []
        for _, row in df.iterrows():
            ground_truth.append({
                'original_start': row['start_time_seconds'],
                'original_end': row['end_time_seconds'],
                'start_seconds': row['start_time_seconds'],  # Will be stretched later
                'end_seconds': row['end_time_seconds'],      # Will be stretched later
                'action': row['action_label'],
                'category': row['category_label'],
                'duration': row['duration_seconds']
            })
        
        self.ground_truth = ground_truth
        print(f"📊 Loaded {len(ground_truth)} ground truth actions from CSV")
        return ground_truth
    
    def set_video_start_time(self, start_time_str):
        """
        Set the video start time to convert HH:MM:SS detections to seconds.
        
        Args:
            start_time_str: Video start time in format "HH:MM:SS"
        """
        try:
            self.video_start_time = datetime.strptime(start_time_str, "%H:%M:%S")
            print(f"📹 Video start time set to: {start_time_str}")
            
            # Convert all detection times to seconds from video start
            for detection in self.detections:
                detection_time = datetime.strptime(detection['time_hms'], "%H:%M:%S")
                time_diff = (detection_time - self.video_start_time).total_seconds()
                detection['time_seconds'] = time_diff
                
            print(f"✅ Converted {len(self.detections)} detection times to video seconds")
            
        except ValueError as e:
            raise ValueError(f"Invalid time format. Use HH:MM:SS. Error: {e}")
    
    def normalize_action_name(self, action):
        """Normalize action names for comparison."""
        action = action.lower().strip()
        
        # Common variations mapping
        mappings = {
            'add food': 'add-food',
            'remove food': 'remove-food',
            'add pan': 'add-pan',
            'remove pan': 'remove-pan',
            'add lid': 'add-lid',
            'remove lid': 'remove-lid',
            'flip': 'flip',
            'season': 'season',
            'stir': 'stir'
        }
        
        return mappings.get(action, action.replace(' ', '-'))
    
    def stretch_ground_truth_timeline(self):
        """Stretch the ground truth timeline to match detection timeline span."""
        if not self.detections or not self.ground_truth:
            return
        
        # Find the span of detections
        detection_times = [d['time_seconds'] for d in self.detections if d['time_seconds'] is not None]
        if not detection_times:
            return
            
        detection_start = min(detection_times)
        detection_end = max(detection_times)
        detection_span = detection_end - detection_start
        
        # Find the span of ground truth
        gt_start = min(gt['original_start'] for gt in self.ground_truth)
        gt_end = max(gt['original_end'] for gt in self.ground_truth)
        gt_span = gt_end - gt_start
        
        # Calculate stretch factor
        if gt_span > 0:
            self.stretch_factor = detection_span / gt_span
        else:
            self.stretch_factor = 1.0
        
        print(f"🔧 Timeline Stretching Analysis:")
        print(f"   Detection timeline: {detection_start:.1f}s to {detection_end:.1f}s (span: {detection_span:.1f}s)")
        print(f"   Original GT timeline: {gt_start:.1f}s to {gt_end:.1f}s (span: {gt_span:.1f}s)")
        print(f"   Stretch factor: {self.stretch_factor:.2f}x")
        
        # Apply stretching to ground truth
        for gt in self.ground_truth:
            # Stretch relative to GT start, then offset to align with detection start
            stretched_start = (gt['original_start'] - gt_start) * self.stretch_factor + detection_start
            stretched_end = (gt['original_end'] - gt_start) * self.stretch_factor + detection_start
            
            gt['start_seconds'] = stretched_start
            gt['end_seconds'] = stretched_end
            gt['stretched_duration'] = stretched_end - stretched_start
        
        print(f"✅ Ground truth timeline stretched by {self.stretch_factor:.2f}x")

    def find_temporal_matches(self):
        """
        Find temporal matches between detections and ground truth.
        
        Returns:
            dict: Analysis results with matches, misses, and false positives
        """
        if not self.video_start_time:
            raise ValueError("Video start time must be set first using set_video_start_time()")
        
        # Apply timeline stretching if enabled
        if self.stretch_timeline:
            self.stretch_ground_truth_timeline()
        
        matches = []
        false_positives = []
        missed_ground_truth = []
        
        # Track which ground truth actions have been matched
        matched_gt_indices = set()
        
        print(f"🔍 Using temporal tolerance: ±{self.tolerance:.1f} seconds")
        if self.stretch_timeline:
            print(f"🔧 Applied timeline stretching: {self.stretch_factor:.2f}x")
        
        # For each detection, find closest ground truth match
        for detection in self.detections:
            detection_time = detection['time_seconds']
            detection_action = self.normalize_action_name(detection['action'])
            
            best_match = None
            best_time_diff = float('inf')
            best_gt_index = None
            
            # Check all ground truth actions
            for i, gt in enumerate(self.ground_truth):
                if i in matched_gt_indices:
                    continue  # Already matched
                
                gt_action = self.normalize_action_name(gt['action'])
                
                # Check if actions match (or are similar)
                actions_match = (detection_action == gt_action or 
                               detection_action in gt_action or 
                               gt_action in detection_action)
                
                if actions_match:
                    # Calculate time difference to stretched GT interval center
                    gt_center = (gt['start_seconds'] + gt['end_seconds']) / 2
                    time_diff = abs(detection_time - gt_center)
                    
                    # Check if detection falls within stretched GT interval or tolerance
                    within_interval = gt['start_seconds'] <= detection_time <= gt['end_seconds']
                    within_tolerance = within_interval or time_diff <= self.tolerance
                    
                    if within_tolerance:
                        if time_diff < best_time_diff:
                            best_match = gt
                            best_time_diff = time_diff
                            best_gt_index = i
            
            if best_match:
                matches.append({
                    'detection': detection,
                    'ground_truth': best_match,
                    'time_diff': best_time_diff,
                    'within_stretched_interval': best_match['start_seconds'] <= detection_time <= best_match['end_seconds'],
                    'original_gt_center': (best_match['original_start'] + best_match['original_end']) / 2,
                    'stretched_gt_center': (best_match['start_seconds'] + best_match['end_seconds']) / 2
                })
                matched_gt_indices.add(best_gt_index)
            else:
                false_positives.append(detection)
        
        # Find unmatched ground truth actions
        for i, gt in enumerate(self.ground_truth):
            if i not in matched_gt_indices:
                missed_ground_truth.append(gt)
        
        return {
            'matches': matches,
            'false_positives': false_positives,
            'missed_ground_truth': missed_ground_truth,
            'total_detections': len(self.detections),
            'total_ground_truth': len(self.ground_truth),
            'stretch_factor': self.stretch_factor
        }
    
    def analyze_performance(self, results):
        """Analyze and print performance metrics."""
        matches = results['matches']
        false_positives = results['false_positives']
        missed_gt = results['missed_ground_truth']
        
        print("\n" + "="*80)
        print("🎯 TIME ALIGNMENT ANALYSIS RESULTS")
        print("="*80)
        
        # Basic metrics
        precision = len(matches) / len(self.detections) if self.detections else 0
        recall = len(matches) / len(self.ground_truth) if self.ground_truth else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\n📊 Performance Metrics:")
        print(f"   Total Detections: {len(self.detections)}")
        print(f"   Total Ground Truth: {len(self.ground_truth)}")
        print(f"   Matches: {len(matches)}")
        print(f"   False Positives: {len(false_positives)}")
        print(f"   Missed Ground Truth: {len(missed_gt)}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall: {recall:.3f}")
        print(f"   F1-Score: {f1_score:.3f}")
        
        if self.stretch_timeline:
            print(f"   Timeline stretch factor: {results['stretch_factor']:.2f}x")
        
        # Temporal analysis
        if matches:
            time_diffs = [m['time_diff'] for m in matches]
            within_interval_count = sum(m['within_stretched_interval'] for m in matches)
            
            print(f"\n⏰ Temporal Alignment:")
            print(f"   Average time difference: {np.mean(time_diffs):.2f}s")
            print(f"   Median time difference: {np.median(time_diffs):.2f}s")
            print(f"   Max time difference: {np.max(time_diffs):.2f}s")
            print(f"   Detections within stretched GT interval: {within_interval_count}/{len(matches)} ({within_interval_count/len(matches)*100:.1f}%)")
        
        # Detailed match analysis
        print(f"\n✅ SUCCESSFUL MATCHES ({len(matches)}):")
        for i, match in enumerate(matches, 1):
            detection = match['detection']
            gt = match['ground_truth']
            time_diff = match['time_diff']
            within = "✓" if match['within_stretched_interval'] else "○"
            
            print(f"   {i}. {detection['time_hms']} ({detection['time_seconds']:.1f}s) → {detection['action']}")
            print(f"      Original GT: {gt['original_start']:.1f}s-{gt['original_end']:.1f}s → {gt['action']}")
            print(f"      Stretched GT: {gt['start_seconds']:.1f}s-{gt['end_seconds']:.1f}s")
            print(f"      Time diff: {time_diff:.1f}s {within}")
        
        # False positives
        if false_positives:
            print(f"\n❌ FALSE POSITIVES ({len(false_positives)}):")
            for i, fp in enumerate(false_positives, 1):
                print(f"   {i}. {fp['time_hms']} ({fp['time_seconds']:.1f}s) → {fp['action']}")
        
        # Missed ground truth
        if missed_gt:
            print(f"\n⏸️  MISSED GROUND TRUTH ({len(missed_gt)}):")
            for i, missed in enumerate(missed_gt, 1):
                print(f"   {i}. Original: {missed['original_start']:.1f}s-{missed['original_end']:.1f}s")
                print(f"      Stretched: {missed['start_seconds']:.1f}s-{missed['end_seconds']:.1f}s → {missed['action']}")
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'avg_time_diff': np.mean(time_diffs) if matches else 0,
            'within_interval_rate': within_interval_count/len(matches) if matches else 0,
            'stretch_factor': results['stretch_factor']
        }
    
    def create_timeline_visualization(self, results, output_path="evaluation/evaluation_results/timeline_alignment.png"):
        """Create a timeline visualization showing detections vs ground truth."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
        
        # Ground truth timeline
        for i, gt in enumerate(self.ground_truth):
            ax1.barh(gt['action'], gt['duration'], 
                    left=gt['start_seconds'], 
                    alpha=0.7, 
                    color='lightblue',
                    edgecolor='blue')
        
        ax1.set_ylabel('Ground Truth Actions')
        ax1.set_title('Ground Truth Timeline')
        ax1.grid(True, alpha=0.3)
        
        # Detection timeline with matches
        detection_y_pos = 0
        colors = {'match': 'green', 'false_positive': 'red'}
        
        for detection in self.detections:
            if detection['time_seconds'] is None:
                continue
                
            # Determine color based on match status
            is_match = any(m['detection'] == detection for m in results['matches'])
            color = colors['match'] if is_match else colors['false_positive']
            
            ax2.scatter(detection['time_seconds'], detection_y_pos, 
                       c=color, s=100, alpha=0.8)
            ax2.annotate(f"{detection['action']}\n{detection['time_hms']}", 
                        (detection['time_seconds'], detection_y_pos),
                        xytext=(0, 10), textcoords='offset points',
                        ha='center', fontsize=8, rotation=45)
            
            detection_y_pos += 0.1
        
        ax2.set_ylabel('Detections')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_title('Detection Timeline (Green=Match, Red=False Positive)')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-0.2, detection_y_pos + 0.2)
        
        plt.tight_layout()
        
        try:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"📈 Timeline visualization saved to: {output_path}")
        except Exception as e:
            print(f"⚠️  Could not save visualization: {e}")
        
        plt.show()

def main():
    """Main function with command line interface."""
    print("🕐 Time Alignment Analyzer with Timeline Stretching")
    print("="*60)
    
    # Parse command line arguments
    if len(sys.argv) < 4:
        print("Usage: python time_alignment_analyzer.py [detection_log] [ground_truth_csv] [video_start_time] [tolerance_seconds] [--no-stretch]")
        print("Example: python time_alignment_analyzer.py detection.log ground_truth.csv 15:17:00 10.0")
        print("Add --no-stretch to disable timeline stretching")
        return
    
    detection_log = sys.argv[1]
    ground_truth_csv = sys.argv[2]
    video_start_time = sys.argv[3]
    
    # Optional tolerance parameter
    tolerance_seconds = 10.0  # Default tolerance
    if len(sys.argv) > 4 and not sys.argv[4].startswith('--'):
        try:
            tolerance_seconds = float(sys.argv[4])
        except ValueError:
            print(f"⚠️  Invalid tolerance value '{sys.argv[4]}', using default: {tolerance_seconds}s")
    
    # Check for --no-stretch flag
    stretch_timeline = '--no-stretch' not in sys.argv
    
    # Initialize analyzer with custom tolerance and stretching option
    analyzer = TimeAlignmentAnalyzer(tolerance_seconds=tolerance_seconds, stretch_timeline=stretch_timeline)
    
    try:
        # Load data
        analyzer.load_detections_from_log(detection_log)
        analyzer.load_ground_truth_from_csv(ground_truth_csv)
        analyzer.set_video_start_time(video_start_time)
        
        # Perform alignment analysis
        results = analyzer.find_temporal_matches()
        metrics = analyzer.analyze_performance(results)
        
        # Create visualization
        analyzer.create_timeline_visualization(results)
        
        print(f"\n✅ Analysis complete!")
        print(f"   Tolerance used: ±{tolerance_seconds:.1f}s")
        if stretch_timeline:
            print(f"   Timeline stretched by: {metrics['stretch_factor']:.2f}x")
        print(f"   F1-Score: {metrics['f1_score']:.3f}")
        print(f"   Average time alignment: {metrics['avg_time_diff']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 