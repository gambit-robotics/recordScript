#!/usr/bin/env python3
"""
Test script to verify log parsing patterns work with Go logging format.
"""

import re

def test_go_log_format():
    """Test the updated regex patterns with Go logging format."""
    
    # Sample Go log output based on the provided code
    go_log_samples = [
        # Acceptance format
        """==========================================
✅ ACTION ACCEPTED: Add Food
   Confidence: 85.2% (≥ 75.0% required)
   Time: 15:17:30
==========================================""",
        
        # Rejection format
        """❌ Action rejected: Remove Pan (45.1% < 75.0%)""",
        
        # No action detected
        """❌ No action detected""",
        
        # Mixed case variations
        """✅ action accepted: Remove Lid
   Confidence: 92.5% (≥ 75.0% required)
   Time: 15:18:45""",
        
        """❌ action rejected: Flip (60.2% < 75.0%)"""
    ]
    
    print("🧪 Testing Go Log Format Compatibility")
    print("=" * 50)
    
    # Test patterns from automate_evaluation.py
    print("\n📋 Testing automate_evaluation.py patterns:")
    
    for i, sample in enumerate(go_log_samples, 1):
        print(f"\n--- Sample {i} ---")
        print(sample)
        
        lines = sample.split('\n')
        current_action = None
        current_confidence = None
        current_time = None
        is_accepted = None
        
        for line in lines:
            # Test acceptance pattern
            if re.search(r'✅ action accepted:', line, re.IGNORECASE) or re.search(r'✅ ACTION ACCEPTED:', line):
                accept_match = re.search(r'✅ (?:action accepted|ACTION ACCEPTED): ([^\n]+)', line, re.IGNORECASE)
                if accept_match:
                    current_action = accept_match.group(1).strip()
                    is_accepted = True
                    print(f"✅ ACCEPTANCE DETECTED: {current_action}")
            
            # Test rejection pattern
            elif re.search(r'❌ action rejected:', line, re.IGNORECASE) or re.search(r'❌ Action rejected:', line):
                reject_match = re.search(r'❌ (?:action rejected|Action rejected): ([^\n]+)', line, re.IGNORECASE)
                if reject_match:
                    current_action = reject_match.group(1).strip()
                    is_accepted = False
                    print(f"❌ REJECTION DETECTED: {current_action}")
            
            # Test confidence pattern
            elif current_action and re.search(r'Confidence: ([\d.]+)%', line):
                confidence_match = re.search(r'Confidence: ([\d.]+)% \(≥ ([\d.]+)% required\)', line)
                if not confidence_match:
                    confidence_match = re.search(r'Confidence: ([\d.]+)% \(< ([\d.]+)%\)', line)
                if confidence_match:
                    current_confidence = confidence_match.group(1)
                    print(f"📊 CONFIDENCE DETECTED: {current_confidence}%")
            
            # Test time pattern
            elif current_action and re.search(r'Time: (\d{2}:\d{2}:\d{2})', line):
                time_match = re.search(r'Time: (\d{2}:\d{2}:\d{2})', line)
                if time_match:
                    current_time = time_match.group(1)
                    print(f"⏰ TIME DETECTED: {current_time}")
        
        if current_action and current_confidence:
            status = "ACCEPTED" if is_accepted else "REJECTED"
            print(f"🎯 FINAL RESULT: {current_action} - {current_confidence}% - {status}")
        elif current_action:
            status = "REJECTED" if is_accepted is False else "UNKNOWN"
            print(f"🎯 FINAL RESULT: {current_action} - {status}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_go_log_format() 