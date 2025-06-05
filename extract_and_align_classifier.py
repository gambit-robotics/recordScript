#!/usr/bin/env python3
"""
Extract classifier results from terminal logs and align with ground truth data.
Single script that handles log parsing, analysis, and performance evaluation.

Usage:
    python extract_and_align_classifier.py [log_file]
    
If no log file is provided, you can paste the terminal output when prompted.
"""

import pandas as pd
import re
import sys
from datetime import datetime
from collections import defaultdict, Counter

def extract_classifier_detections(log_text):
    """Extract classifier action detections from terminal log text."""
    detections = []
    
    # Pattern to match action detection lines - cleaner pattern
    action_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z).*🍳 Burner (\d+): ([^{]+)'
    confidence_pattern = r'📊 Confidence: ([\d.]+)%.*?Duration: ([\d.]+)s'
    
    lines = log_text.split('\n')
    
    for i, line in enumerate(lines):
        # Look for action detection
        action_match = re.search(action_pattern, line)
        if action_match:
            timestamp_str = action_match.group(1)
            burner_id = int(action_match.group(2))
            action = action_match.group(3).strip()
            
            # Look for confidence/duration in next few lines
            confidence = None
            duration = None
            for j in range(i+1, min(i+5, len(lines))):
                conf_match = re.search(confidence_pattern, lines[j])
                if conf_match:
                    confidence = float(conf_match.group(1))
                    duration = float(conf_match.group(2))
                    break
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M:%S')
            except:
                time_str = timestamp_str.split('T')[1][:8]
            
            detections.append({
                'timestamp': time_str,
                'burner_id': burner_id,
                'action': action,
                'confidence': confidence,
                'duration': duration,
                'raw_line': line.strip()
            })
    
    return detections

def extract_food_detections(log_text):
    """Extract food detection events from logs."""
    food_detections = []
    
    # Pattern for food detection
    food_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z).*Food detected and added to cache: (.+?) \(confidence: ([\d.]+)\)'
    
    matches = re.finditer(food_pattern, log_text)
    for match in matches:
        timestamp_str = match.group(1)
        food_type = match.group(2)
        confidence = float(match.group(3))
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            time_str = timestamp.strftime('%H:%M:%S')
        except:
            time_str = timestamp_str.split('T')[1][:8]
        
        food_detections.append({
            'timestamp': time_str,
            'food_type': food_type,
            'confidence': confidence
        })
    
    return food_detections

def load_ground_truth(csv_file="ml_dataset.csv"):
    """Load ground truth data from CSV file."""
    try:
        df = pd.read_csv(csv_file)
        return df
    except FileNotFoundError:
        print(f"❌ Ground truth file {csv_file} not found")
        return None
    except Exception as e:
        print(f"❌ Error loading ground truth: {e}")
        return None

def normalize_action(action):
    """Normalize action names for comparison."""
    action = action.lower().strip()
    
    # Common variations
    mappings = {
        'remove lid': 'remove-lid',
        'add lid': 'add-lid', 
        'remove food': 'remove-food',
        'add food': 'add-food',
        'flip': 'flip',
        'remove pan': 'remove-pan',
        'add pan': 'add-pan'
    }
    
    return mappings.get(action, action.replace(' ', '-'))

def analyze_performance(detections, ground_truth_df):
    """Analyze classifier performance against ground truth."""
    print("🔍 Classifier Performance Analysis")
    print("=" * 60)
    
    # Ground truth summary
    if ground_truth_df is not None:
        gt_counts = ground_truth_df['action_label'].value_counts()
        
        print("📊 Ground Truth Dataset:")
        print(f"   Total labeled segments: {len(ground_truth_df)}")
        for action, count in gt_counts.items():
            print(f"   {action}: {count} occurrences")
    else:
        print("📊 No ground truth data available")
        gt_counts = pd.Series(dtype=int)
    
    print(f"\n🔍 Classifier Detections:")
    print(f"   Total detections: {len(detections)}")
    
    # Count detections by action type
    detection_counts = Counter()
    for det in detections:
        normalized_action = normalize_action(det['action'])
        detection_counts[normalized_action] += 1
    
    for action, count in detection_counts.items():
        print(f"   {action}: {count} detections")
    
    if ground_truth_df is not None:
        print(f"\n🎯 Performance Comparison:")
        
        total_detected = 0
        total_expected = 0
        
        # Analyze each action type
        all_actions = set(list(gt_counts.index) + list(detection_counts.keys()))
        
        for action in sorted(all_actions):
            expected = gt_counts.get(action, 0)
            detected = detection_counts.get(action, 0)
            
            total_expected += expected
            total_detected += detected
            
            if expected > 0:
                recall = detected / expected
                status = "✅" if recall >= 0.8 else "⚠️" if recall >= 0.5 else "❌"
            else:
                recall = 0
                status = "➖" if detected == 0 else "🔄"  # 🔄 for extra detections
            
            print(f"   {action:15} | Expected: {expected:2d} | Detected: {detected:2d} | Recall: {recall:6.1%} {status}")
        
        # Overall metrics
        overall_recall = total_detected / total_expected if total_expected > 0 else 0
        print(f"\n📈 Overall Performance:")
        print(f"   Total Recall: {overall_recall:.1%}")
        print(f"   Coverage: {total_detected}/{total_expected} actions detected")
    
    # Confidence analysis
    if detections:
        confidences = [d['confidence'] for d in detections if d['confidence'] is not None]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            min_confidence = min(confidences)
            max_confidence = max(confidences)
            
            print(f"\n🎯 Confidence Analysis:")
            print(f"   Average confidence: {avg_confidence:.1f}%")
            print(f"   Range: {min_confidence:.1f}% - {max_confidence:.1f}%")
            
            high_conf = len([c for c in confidences if c >= 80])
            med_conf = len([c for c in confidences if 60 <= c < 80])
            low_conf = len([c for c in confidences if c < 60])
            
            print(f"   High confidence (≥80%): {high_conf}/{len(confidences)}")
            print(f"   Medium confidence (60-79%): {med_conf}/{len(confidences)}")
            print(f"   Low confidence (<60%): {low_conf}/{len(confidences)}")
    
    # Detection timeline
    print(f"\n⏰ Detection Timeline:")
    for i, det in enumerate(detections, 1):
        conf_str = f"{det['confidence']:5.1f}%" if det['confidence'] else "  N/A"
        dur_str = f"{det['duration']:4.1f}s" if det['duration'] else " N/A"
        print(f"   {i:2d}. {det['timestamp']} | {det['action']:15} | {conf_str} | {dur_str}")
    
    return detection_counts, gt_counts

def provide_insights(detections, detection_counts, gt_counts):
    """Provide actionable insights and recommendations."""
    print(f"\n💡 Key Insights:")
    
    if not detections:
        print("   • No classifier detections found in logs")
        print("   • Check if classification is running and logging properly")
        return
    
    # Confidence insights
    confidences = [d['confidence'] for d in detections if d['confidence'] is not None]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        
        if avg_confidence >= 85:
            print(f"   • High average confidence ({avg_confidence:.1f}%) indicates good model certainty")
        elif avg_confidence >= 70:
            print(f"   • Moderate confidence ({avg_confidence:.1f}%) - consider threshold tuning")
        else:
            print(f"   • Low confidence ({avg_confidence:.1f}%) - model may need retraining")
        
        low_conf_count = len([c for c in confidences if c < 70])
        if low_conf_count > 0:
            print(f"   • {low_conf_count} low-confidence detections may be false positives")
    
    # Action balance insights
    if 'remove-lid' in detection_counts and 'add-lid' in detection_counts:
        lid_ratio = detection_counts['add-lid'] / detection_counts['remove-lid']
        print(f"   • Lid manipulation ratio (add/remove): {lid_ratio:.2f}")
        if abs(lid_ratio - 1.0) > 0.3:
            print("   • Imbalanced lid actions - check for missed detections")
    
    if 'add-food' in detection_counts and 'remove-food' in detection_counts:
        food_ratio = detection_counts['add-food'] / detection_counts['remove-food']
        print(f"   • Food manipulation ratio (add/remove): {food_ratio:.2f}")
    
    # Missing critical actions
    expected_actions = ['add-pan', 'remove-pan', 'add-food', 'remove-food']
    missing_actions = [action for action in expected_actions if detection_counts.get(action, 0) == 0]
    if missing_actions:
        print(f"   • Missing critical actions: {', '.join(missing_actions)}")
    
    print(f"\n📝 Recommendations:")
    
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        if avg_conf >= 80:
            print(f"   • Set confidence threshold around 75-80% to filter noise")
        else:
            print(f"   • Set confidence threshold around 65-70% to avoid missing actions")
    
    print(f"   • Implement temporal smoothing to reduce duplicate detections")
    print(f"   • Add action sequence validation (logical flow checking)")
    
    if len(gt_counts) > 0:
        total_expected = sum(gt_counts.values)  # Fixed: removed () from .values
        total_detected = len(detections)
        if total_detected < total_expected * 0.7:
            print(f"   • Low detection rate - consider lowering confidence threshold")
        elif total_detected > total_expected * 1.3:
            print(f"   • High detection rate - may have false positives, raise threshold")
    
    print(f"   • Review video manually to validate detection timing accuracy")

def export_classification_lines(log_text, detections, output_file="classification_timeline.log"):
    """Export just the classification result lines to a separate log file."""
    try:
        with open(output_file, 'w') as f:
            f.write("# Classifier Detection Timeline\n")
            f.write("# Extracted classification results in chronological order\n")
            f.write("# Format: [timestamp] [action] [confidence] [duration]\n")
            f.write("=" * 80 + "\n\n")
            
            # Write detection summary
            f.write(f"Total detections found: {len(detections)}\n\n")
            
            # Extract and write the relevant log lines
            lines = log_text.split('\n')
            classification_lines = []
            
            for detection in detections:
                # Find the original log lines for this detection
                action_line = detection['raw_line']
                
                # Look for the confidence line that follows
                for i, line in enumerate(lines):
                    if action_line in line:
                        # Found the action line, now look for confidence in next few lines
                        classification_lines.append(f"# Detection {len(classification_lines) + 1}")
                        classification_lines.append(line)
                        
                        for j in range(i+1, min(i+5, len(lines))):
                            if "📊 Confidence:" in lines[j]:
                                classification_lines.append(lines[j])
                                break
                        
                        # Add food detection if it exists around this time
                        timestamp_str = detection['timestamp']
                        for k in range(max(0, i-10), min(len(lines), i+10)):
                            if "Food detected and added to cache:" in lines[k] and timestamp_str.replace(':', '') in lines[k]:
                                classification_lines.append(lines[k])
                        
                        classification_lines.append("")  # Empty line for separation
                        break
            
            # Write all classification lines
            for line in classification_lines:
                f.write(line + "\n")
            
            # Add summary at the end
            f.write("\n" + "=" * 80 + "\n")
            f.write("# Summary\n")
            
            action_counts = {}
            for det in detections:
                action = det['action']
                if action not in action_counts:
                    action_counts[action] = 0
                action_counts[action] += 1
            
            f.write(f"# Total detections: {len(detections)}\n")
            for action, count in sorted(action_counts.items()):
                f.write(f"# {action}: {count} detections\n")
            
            if detections:
                confidences = [d['confidence'] for d in detections if d['confidence'] is not None]
                if confidences:
                    avg_conf = sum(confidences) / len(confidences)
                    f.write(f"# Average confidence: {avg_conf:.1f}%\n")
        
        print(f"📝 Classification timeline exported to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting classification lines: {e}")
        return False

def main():
    """Main function to run the analysis."""
    print("🔄 Classifier Log Analysis & Ground Truth Alignment")
    print("=" * 60)
    
    # Get log data
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        try:
            with open(log_file, 'r') as f:
                log_text = f.read()
            print(f"📂 Loaded log file: {log_file}")
        except FileNotFoundError:
            print(f"❌ Log file {log_file} not found")
            return
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
            return
    else:
        print("📋 No log file provided. Please paste your terminal logs below.")
        print("   (Paste the logs and press Ctrl+D when done, or Ctrl+C to cancel)")
        print("-" * 60)
        
        try:
            log_lines = []
            while True:
                try:
                    line = input()
                    log_lines.append(line)
                except EOFError:
                    break
            log_text = '\n'.join(log_lines)
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            return
        
        if not log_text.strip():
            print("❌ No log data provided")
            return
    
    print(f"\n🔍 Analyzing log data ({len(log_text)} characters)...")
    
    # Extract detections
    detections = extract_classifier_detections(log_text)
    food_detections = extract_food_detections(log_text)
    
    # Export classification timeline first
    if detections:
        base_name = sys.argv[1].replace('.txt', '').replace('.log', '') if len(sys.argv) > 1 else 'classification'
        timeline_file = f"{base_name}_timeline.log"
        export_classification_lines(log_text, detections, timeline_file)
    
    if food_detections:
        print(f"\n🍽️  Food Detections Found:")
        for food in food_detections:
            print(f"   {food['timestamp']} | {food['food_type']} | {food['confidence']:.2f} conf")
    
    # Load ground truth
    ground_truth_df = load_ground_truth()
    
    # Analyze performance
    detection_counts, gt_counts = analyze_performance(detections, ground_truth_df)
    
    # Provide insights
    provide_insights(detections, detection_counts, gt_counts)
    
    print(f"\n✅ Analysis complete!")
    
    # Summary
    if detections:
        print(f"\n📋 Summary:")
        print(f"   • {len(detections)} action detections extracted from logs")
        if ground_truth_df is not None:
            total_gt = len(ground_truth_df)
            coverage = len(detections) / total_gt * 100 if total_gt > 0 else 0
            print(f"   • {coverage:.1f}% coverage of expected actions")
        if food_detections:
            print(f"   • {len(food_detections)} food detection events")
        
        confidences_with_values = [d['confidence'] for d in detections if d['confidence'] is not None]
        if confidences_with_values:
            avg_conf = sum(confidences_with_values) / len(confidences_with_values)
            print(f"   • {avg_conf:.1f}% average detection confidence")
        
        # Mention the exported timeline file
        base_name = sys.argv[1].replace('.txt', '').replace('.log', '') if len(sys.argv) > 1 else 'classification'
        timeline_file = f"{base_name}_timeline.log"
        print(f"   • Classification timeline saved to: {timeline_file}")

if __name__ == "__main__":
    main() 