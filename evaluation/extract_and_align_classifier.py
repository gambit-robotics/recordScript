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
    
    # New pattern to match the structured log format
    lines = log_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for start of motion detection block
        if "🎬 ===== MOTION DETECTED ===== 🎬" in line:
            # Initialize detection data
            detection = {
                'timestamp': None,
                'burner_id': None,  # Not used in new format
                'action': None,
                'confidence': None,
                'duration': None,
                'analysis_duration': None,
                'similarity': None,
                'accepted': False,
                'raw_lines': []
            }
            
            # Capture all lines in this detection block
            block_start = i
            
            # Parse the motion detected section
            while i < len(lines) and not "📋 ===== CLAUDE RESPONSE ===== 📋" in lines[i]:
                detection['raw_lines'].append(lines[i])
                
                # Extract similarity and threshold
                if "📊 Similarity:" in lines[i]:
                    similarity_match = re.search(r'📊 Similarity: ([\d.]+)%', lines[i])
                    if similarity_match:
                        detection['similarity'] = float(similarity_match.group(1))
                
                # Extract time and duration
                elif "⏰ Time:" in lines[i]:
                    time_match = re.search(r'⏰ Time: (\d{2}:\d{2}:\d{2}).*?Duration: ([\d.]+)s', lines[i])
                    if time_match:
                        detection['timestamp'] = time_match.group(1)
                        detection['duration'] = float(time_match.group(2))
                
                i += 1
            
            # Parse Claude response section - we're now at the CLAUDE RESPONSE line
            while i < len(lines) and not "📋 ===========================" in lines[i]:
                detection['raw_lines'].append(lines[i])
                
                # Extract detected action
                if "🎭 Detected Action:" in lines[i]:
                    action_match = re.search(r'🎭 Detected Action: ([^{"\s]+(?:\s+[^{"\s]+)*)', lines[i])
                    if action_match:
                        detection['action'] = action_match.group(1).strip()
                
                # Extract confidence
                elif "🎯 Confidence:" in lines[i]:
                    conf_match = re.search(r'🎯 Confidence: ([\d.]+)%', lines[i])
                    if conf_match:
                        detection['confidence'] = float(conf_match.group(1))
                
                # Extract analysis duration
                elif "⏱️  Analysis Duration:" in lines[i]:
                    dur_match = re.search(r'⏱️  Analysis Duration: ([\d.]+)s', lines[i])
                    if dur_match:
                        detection['analysis_duration'] = float(dur_match.group(1))
                
                i += 1
            
            # Look for acceptance line after the closing line
            if i < len(lines):
                detection['raw_lines'].append(lines[i])  # Add the closing line
                i += 1
                
                # Check next few lines for acceptance/rejection
                for j in range(i, min(i + 5, len(lines))):  # Increased range to check more lines
                    if "✅ Action ACCEPTED:" in lines[j]:
                        detection['accepted'] = True
                        detection['raw_lines'].append(lines[j])
                        break
                    elif "❌ Action REJECTED:" in lines[j]:
                        detection['accepted'] = False
                        detection['raw_lines'].append(lines[j])
                        break
                    elif "❌ No action detected" in lines[j]:
                        detection['accepted'] = False
                        detection['raw_lines'].append(lines[j])
                        break
            
            # Only add detection if we found the essential components and it's not "(none)"
            if (detection['action'] and 
                detection['confidence'] is not None and 
                detection['timestamp'] and
                detection['action'].lower().strip() != "(none)"):
                detection['raw_line'] = f"{detection['timestamp']} | {detection['action']} | {detection['confidence']}%"
                detections.append(detection)
        
        i += 1
    
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

def load_ground_truth(csv_file="../data/datasets/ml_dataset.csv"):
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
    
    # Separate accepted vs rejected detections
    accepted_detections = [d for d in detections if d.get('accepted', True)]  # Default to accepted if not specified
    rejected_detections = [d for d in detections if not d.get('accepted', True)]
    
    print(f"   Accepted detections: {len(accepted_detections)}")
    print(f"   Rejected detections: {len(rejected_detections)}")
    
    # Count detections by action type (only accepted ones for main analysis)
    detection_counts = Counter()
    for det in accepted_detections:
        normalized_action = normalize_action(det['action'])
        detection_counts[normalized_action] += 1
    
    print(f"\n📊 Accepted Detection Breakdown:")
    for action, count in detection_counts.items():
        print(f"   {action}: {count} detections")
    
    if rejected_detections:
        print(f"\n❌ Rejected Detection Breakdown:")
        rejected_counts = Counter()
        for det in rejected_detections:
            normalized_action = normalize_action(det['action'])
            rejected_counts[normalized_action] += 1
        for action, count in rejected_counts.items():
            print(f"   {action}: {count} rejected")
    
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
    
    # Similarity analysis (new field)
    similarities = [d['similarity'] for d in detections if d.get('similarity') is not None]
    if similarities:
        avg_similarity = sum(similarities) / len(similarities)
        min_similarity = min(similarities)
        max_similarity = max(similarities)
        
        print(f"\n📊 Motion Similarity Analysis:")
        print(f"   Average similarity: {avg_similarity:.1f}%")
        print(f"   Range: {min_similarity:.1f}% - {max_similarity:.1f}%")
    
    # Analysis duration stats (new field)
    analysis_durations = [d['analysis_duration'] for d in detections if d.get('analysis_duration') is not None]
    if analysis_durations:
        avg_analysis_duration = sum(analysis_durations) / len(analysis_durations)
        min_analysis_duration = min(analysis_durations)
        max_analysis_duration = max(analysis_durations)
        
        print(f"\n⚡ Analysis Performance:")
        print(f"   Average analysis time: {avg_analysis_duration:.1f}s")
        print(f"   Range: {min_analysis_duration:.1f}s - {max_analysis_duration:.1f}s")
        
        slow_analyses = len([d for d in analysis_durations if d > 5.0])
        if slow_analyses > 0:
            print(f"   Slow analyses (>5s): {slow_analyses}/{len(analysis_durations)}")
    
    # Detection timeline
    print(f"\n⏰ Detection Timeline:")
    for i, det in enumerate(detections, 1):
        conf_str = f"{det['confidence']:5.1f}%" if det['confidence'] else "  N/A"
        dur_str = f"{det['duration']:4.1f}s" if det['duration'] else " N/A"
        sim_str = f"{det['similarity']:5.1f}%" if det.get('similarity') else "  N/A"
        status_str = "✅" if det.get('accepted', True) else "❌"
        
        print(f"   {i:2d}. {det['timestamp']} | {det['action']:15} | Conf:{conf_str} | Sim:{sim_str} | {dur_str} | {status_str}")
    
    return detection_counts, gt_counts

def provide_insights(detections, detection_counts, gt_counts):
    """Provide actionable insights and recommendations."""
    print(f"\n💡 Key Insights:")
    
    if not detections:
        print("   • No classifier detections found in logs")
        print("   • Check if classification is running and logging properly")
        return
    
    # Acceptance rate analysis
    accepted_count = len([d for d in detections if d.get('accepted', True)])
    rejected_count = len([d for d in detections if not d.get('accepted', True)])
    total_count = len(detections)
    
    if rejected_count > 0:
        acceptance_rate = accepted_count / total_count
        print(f"   • Acceptance rate: {acceptance_rate:.1%} ({accepted_count}/{total_count} detections)")
        
        if acceptance_rate < 0.7:
            print("   • Low acceptance rate suggests confidence threshold may be too low")
        elif acceptance_rate > 0.95:
            print("   • Very high acceptance rate - consider lowering confidence threshold")
    
    # Confidence insights
    confidences = [d['confidence'] for d in detections if d['confidence'] is not None]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        
        # Separate accepted vs rejected confidence stats
        accepted_confidences = [d['confidence'] for d in detections if d.get('accepted', True) and d['confidence'] is not None]
        rejected_confidences = [d['confidence'] for d in detections if not d.get('accepted', True) and d['confidence'] is not None]
        
        print(f"   • Average confidence: {avg_confidence:.1f}%")
        
        if accepted_confidences and rejected_confidences:
            avg_accepted = sum(accepted_confidences) / len(accepted_confidences)
            avg_rejected = sum(rejected_confidences) / len(rejected_confidences)
            print(f"   • Accepted avg: {avg_accepted:.1f}%, Rejected avg: {avg_rejected:.1f}%")
        
        if avg_confidence >= 85:
            print(f"   • High average confidence indicates good model certainty")
        elif avg_confidence >= 70:
            print(f"   • Moderate confidence - consider threshold tuning")
        else:
            print(f"   • Low confidence - model may need retraining")
        
        low_conf_count = len([c for c in confidences if c < 70])
        if low_conf_count > 0:
            print(f"   • {low_conf_count} low-confidence detections may be false positives")
    
    # Similarity insights
    similarities = [d['similarity'] for d in detections if d.get('similarity') is not None]
    if similarities:
        avg_similarity = sum(similarities) / len(similarities)
        low_sim_count = len([s for s in similarities if s < 75])
        
        print(f"   • Average motion similarity: {avg_similarity:.1f}%")
        if low_sim_count > 0:
            print(f"   • {low_sim_count} detections with low motion similarity (<75%)")
        
        if avg_similarity < 80:
            print("   • Low motion similarity suggests noisy motion detection")
    
    # Analysis performance insights
    analysis_durations = [d['analysis_duration'] for d in detections if d.get('analysis_duration') is not None]
    if analysis_durations:
        avg_analysis_time = sum(analysis_durations) / len(analysis_durations)
        slow_count = len([d for d in analysis_durations if d > 5.0])
        
        print(f"   • Average analysis time: {avg_analysis_time:.1f}s")
        if slow_count > 0:
            print(f"   • {slow_count} slow analyses (>5s) may indicate processing bottlenecks")
        
        if avg_analysis_time > 4.0:
            print("   • Slow analysis times - consider optimizing model inference")
    
    # Action balance insights (only for accepted detections)
    accepted_detection_counts = Counter()
    for det in detections:
        if det.get('accepted', True):
            normalized_action = normalize_action(det['action'])
            accepted_detection_counts[normalized_action] += 1
    
    if 'remove-lid' in accepted_detection_counts and 'add-lid' in accepted_detection_counts:
        lid_ratio = accepted_detection_counts['add-lid'] / accepted_detection_counts['remove-lid']
        print(f"   • Lid manipulation ratio (add/remove): {lid_ratio:.2f}")
        if abs(lid_ratio - 1.0) > 0.3:
            print("   • Imbalanced lid actions - check for missed detections")
    
    if 'add-food' in accepted_detection_counts and 'remove-food' in accepted_detection_counts:
        food_ratio = accepted_detection_counts['add-food'] / accepted_detection_counts['remove-food']
        print(f"   • Food manipulation ratio (add/remove): {food_ratio:.2f}")
    
    # Missing critical actions
    expected_actions = ['add-pan', 'remove-pan', 'add-food', 'remove-food']
    missing_actions = [action for action in expected_actions if accepted_detection_counts.get(action, 0) == 0]
    if missing_actions:
        print(f"   • Missing critical actions: {', '.join(missing_actions)}")
    
    print(f"\n📝 Recommendations:")
    
    # Confidence threshold recommendations
    if confidences:
        if rejected_count > 0:
            # We have rejection data, so analyze the threshold effectiveness
            rejected_confidences = [d['confidence'] for d in detections if not d.get('accepted', True) and d['confidence'] is not None]
            if rejected_confidences:
                max_rejected_conf = max(rejected_confidences)
                print(f"   • Current threshold appears effective (highest rejected: {max_rejected_conf:.1f}%)")
            else:
                avg_conf = sum(confidences) / len(confidences)
                if avg_conf >= 80:
                    print(f"   • Consider confidence threshold around 75-80% to filter noise")
                else:
                    print(f"   • Consider confidence threshold around 65-70% to avoid missing actions")
        else:
            # No rejection data, use traditional analysis
            avg_conf = sum(confidences) / len(confidences)
            if avg_conf >= 80:
                print(f"   • Set confidence threshold around 75-80% to filter noise")
            else:
                print(f"   • Set confidence threshold around 65-70% to avoid missing actions")
    
    # Motion similarity recommendations
    if similarities:
        avg_sim = sum(similarities) / len(similarities)
        if avg_sim < 85:
            print(f"   • Consider raising motion similarity threshold to reduce false triggers")
    
    # Performance recommendations
    if analysis_durations:
        avg_time = sum(analysis_durations) / len(analysis_durations)
        if avg_time > 3.0:
            print(f"   • Optimize model inference speed (current avg: {avg_time:.1f}s)")
    
    print(f"   • Implement temporal smoothing to reduce duplicate detections")
    print(f"   • Add action sequence validation (logical flow checking)")
    
    if len(gt_counts) > 0:
        total_expected = sum(gt_counts.values)
        total_detected = len([d for d in detections if d.get('accepted', True)])
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
            f.write("# New Format: Motion Detection + Claude Analysis + Acceptance\n")
            f.write("=" * 80 + "\n\n")
            
            # Write detection summary
            f.write(f"Total detections found: {len(detections)}\n")
            accepted_count = len([d for d in detections if d.get('accepted', True)])
            rejected_count = len([d for d in detections if not d.get('accepted', True)])
            f.write(f"Accepted: {accepted_count}, Rejected: {rejected_count}\n\n")
            
            # Extract and write the structured log blocks
            for i, detection in enumerate(detections, 1):
                f.write(f"# Detection {i} - {detection['timestamp']} - {detection['action']}\n")
                f.write(f"# Status: {'ACCEPTED' if detection.get('accepted', True) else 'REJECTED'}\n")
                
                # Write all the raw lines for this detection
                if 'raw_lines' in detection:
                    for line in detection['raw_lines']:
                        f.write(line + "\n")
                else:
                    # Fallback to basic info if raw_lines not available
                    f.write(f"Time: {detection['timestamp']}\n")
                    f.write(f"Action: {detection['action']}\n")
                    f.write(f"Confidence: {detection['confidence']}%\n")
                    if detection.get('similarity'):
                        f.write(f"Similarity: {detection['similarity']}%\n")
                    if detection.get('duration'):
                        f.write(f"Duration: {detection['duration']}s\n")
                    if detection.get('analysis_duration'):
                        f.write(f"Analysis Duration: {detection['analysis_duration']}s\n")
                
                f.write("\n" + "-" * 60 + "\n\n")
            
            # Add comprehensive summary at the end
            f.write("\n" + "=" * 80 + "\n")
            f.write("# ANALYSIS SUMMARY\n")
            f.write("=" * 80 + "\n")
            
            # Action breakdown
            action_counts = {}
            accepted_action_counts = {}
            rejected_action_counts = {}
            
            for det in detections:
                action = det['action']
                if action not in action_counts:
                    action_counts[action] = 0
                action_counts[action] += 1
                
                if det.get('accepted', True):
                    if action not in accepted_action_counts:
                        accepted_action_counts[action] = 0
                    accepted_action_counts[action] += 1
                else:
                    if action not in rejected_action_counts:
                        rejected_action_counts[action] = 0
                    rejected_action_counts[action] += 1
            
            f.write(f"\n# Detection Counts by Action:\n")
            for action, count in sorted(action_counts.items()):
                accepted = accepted_action_counts.get(action, 0)
                rejected = rejected_action_counts.get(action, 0)
                f.write(f"# {action}: {count} total (✅{accepted} accepted, ❌{rejected} rejected)\n")
            
            # Stats summary
            if detections:
                confidences = [d['confidence'] for d in detections if d['confidence'] is not None]
                similarities = [d['similarity'] for d in detections if d.get('similarity') is not None]
                analysis_durations = [d['analysis_duration'] for d in detections if d.get('analysis_duration') is not None]
                
                f.write(f"\n# Performance Statistics:\n")
                f.write(f"# Total detections: {len(detections)}\n")
                f.write(f"# Acceptance rate: {accepted_count}/{len(detections)} ({accepted_count/len(detections)*100:.1f}%)\n")
                
                if confidences:
                    avg_conf = sum(confidences) / len(confidences)
                    f.write(f"# Average confidence: {avg_conf:.1f}%\n")
                    f.write(f"# Confidence range: {min(confidences):.1f}% - {max(confidences):.1f}%\n")
                
                if similarities:
                    avg_sim = sum(similarities) / len(similarities)
                    f.write(f"# Average similarity: {avg_sim:.1f}%\n")
                    f.write(f"# Similarity range: {min(similarities):.1f}% - {max(similarities):.1f}%\n")
                
                if analysis_durations:
                    avg_analysis = sum(analysis_durations) / len(analysis_durations)
                    f.write(f"# Average analysis time: {avg_analysis:.1f}s\n")
                    f.write(f"# Analysis time range: {min(analysis_durations):.1f}s - {max(analysis_durations):.1f}s\n")
                
                # Timeline summary
                f.write(f"\n# Timeline Summary:\n")
                f.write(f"# First detection: {detections[0]['timestamp']} - {detections[0]['action']}\n")
                f.write(f"# Last detection: {detections[-1]['timestamp']} - {detections[-1]['action']}\n")
        
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