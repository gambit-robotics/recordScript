#!/usr/bin/env python3
"""
Viam Camera Recording Launcher
Choose between basic recording or interactive coaching mode.
"""

import sys
import subprocess

def main():
    print("🎥 Viam Camera Recording")
    print("=" * 40)
    print("Choose your recording mode:")
    print()
    print("1. Basic Recording - Simple video capture")
    print("2. Interactive Coaching - Guided cooking actions")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1 or 2): ").strip()
            
            if choice == "1":
                print("\n🎬 Starting basic recording...")
                subprocess.run([sys.executable, "record_rgb.py"])
                break
            elif choice == "2":
                print("\n🍳 Starting interactive coaching session...")
                subprocess.run([sys.executable, "record_rgb_interactive.py"])
                break
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 