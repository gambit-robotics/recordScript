#!/usr/bin/env python3
"""
Automated Evaluation Pipeline for Viam Action Classifier

This script automates the entire evaluation process:
1. Updates video files in Viam cloud machine configuration via API
2. Runs viam-server and captures logs
3. Detects when video playback completes
4. Runs classification analysis
5. Generates comprehensive reports

Usage:
    python automate_evaluation.py --videos video1.mp4 video2.mp4 video3.mp4 video4.mp4
    python automate_evaluation.py --video-dir /path/to/videos
    python automate_evaluation.py --config config.json

Requirements:
    pip install viam-sdk
"""

import os
import sys
import json
import time
import signal
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import threading
import queue
import asyncio

# Viam API imports
from viam.app.viam_client import ViamClient
from viam.rpc.dial import DialOptions, Credentials

class EvaluationPipeline:
    def __init__(self, viam_config_path, videos, output_dir="evaluation_results", machine_id=None):
        self.viam_config_path = Path(viam_config_path)
        self.videos = [Path(v) for v in videos]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load Viam credentials
        with open(self.viam_config_path, 'r') as f:
            self.viam_config = json.load(f)
        
        # Extract machine ID from cloud config or use provided one
        self.machine_id = machine_id or self.viam_config.get("cloud", {}).get("id")
        if not self.machine_id:
            raise ValueError("Machine ID not found in config and not provided")
        
        self.current_process = None
        self.log_queue = queue.Queue()
        self.original_machine_config = None
        
        # Results tracking
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'videos': [],
            'summary': {},
            'machine_id': self.machine_id
        }
    
    async def get_viam_client(self):
        """Create and return a Viam API client."""
        try:
            # Extract credentials from config
            cloud_config = self.viam_config.get("cloud", {})
            
            # Create credentials - this may need adjustment based on your auth method
            creds = Credentials(
                type="robot-location-secret",
                payload=cloud_config.get("secret", "")
            )
            
            opts = DialOptions(
                credentials=creds,
                app_address=cloud_config.get("app_address", "https://app.viam.com:443")
            )
            
            return await ViamClient.create_from_dial_options(opts)
        
        except Exception as e:
            print(f"❌ Failed to create Viam client: {e}")
            print("💡 You may need to install the Viam SDK: pip install viam-sdk")
            raise
    
    async def get_machine_config(self):
        """Fetch the current machine configuration from Viam cloud."""
        print(f"📡 Fetching machine config for: {self.machine_id}")
        
        try:
            client = await self.get_viam_client()
            
            # Get machine configuration
            config = await client.get_robot_config(robot_id=self.machine_id)
            
            await client.close()
            return config
            
        except Exception as e:
            print(f"❌ Failed to fetch machine config: {e}")
            raise
    
    async def update_machine_config(self, new_config):
        """Update the machine configuration on Viam cloud."""
        print(f"📤 Updating machine config for: {self.machine_id}")
        
        try:
            client = await self.get_viam_client()
            
            # Update machine configuration
            await client.update_robot_config(robot_id=self.machine_id, config=new_config)
            
            await client.close()
            print("✅ Machine config updated successfully")
            
        except Exception as e:
            print(f"❌ Failed to update machine config: {e}")
            raise
    
    async def update_video_path(self, video_path):
        """Update the video path in the replayCamera-1 component."""
        print(f"🔧 Updating video path to: {video_path}")
        
        # Get current config
        config = await self.get_machine_config()
        
        # Backup original config on first run
        if self.original_machine_config is None:
            self.original_machine_config = json.loads(json.dumps(config))  # Deep copy
            print("📋 Backed up original machine config")
        
        # Find and update the replayCamera-1 component
        updated = False
        for component in config.get("components", []):
            if component.get("name") == "replayCamera-1":
                if "attributes" not in component:
                    component["attributes"] = {}
                component["attributes"]["video_path"] = str(video_path.absolute())
                updated = True
                print(f"✅ Updated replayCamera-1 video_path: {video_path.name}")
                break
        
        if not updated:
            print("❌ replayCamera-1 component not found in config")
            raise ValueError("replayCamera-1 component not found")
        
        # Update the config on Viam cloud
        await self.update_machine_config(config)
        
        # Wait a moment for the config to propagate
        await asyncio.sleep(2)
    
    def run_viam_server(self, video_path, timeout_minutes=10):
        """Run viam-server and capture logs until video finishes or timeout."""
        print(f"\n🚀 Starting viam-server for: {video_path.name}")
        print(f"⏱️  Timeout: {timeout_minutes} minutes")
        
        # Prepare log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.output_dir / f"{video_path.stem}_{timestamp}.log"
        
        try:
            # Start viam-server process
            cmd = ["viam-server", "-config", str(self.viam_config_path)]
            print(f"🔧 Command: {' '.join(cmd)}")
            
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Start log monitoring in separate thread
            log_thread = threading.Thread(
                target=self._monitor_logs,
                args=(self.current_process.stdout, log_file)
            )
            log_thread.daemon = True
            log_thread.start()
            
            # Wait for completion or timeout
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            video_finished = False
            
            print(f"📺 Monitoring logs for end-of-file signal...")
            print(f"📝 Logs being written to: {log_file}")
            
            while True:
                # Check if process is still running
                if self.current_process.poll() is not None:
                    print("🔴 Viam-server process ended")
                    break
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    print(f"⏰ Timeout reached ({timeout_minutes} minutes)")
                    break
                
                # Check log queue for end-of-file signal
                try:
                    log_line = self.log_queue.get_nowait()
                    if "End of file" in log_line and "stopping playback" in log_line:
                        print("🎬 Video playback completed!")
                        video_finished = True
                        time.sleep(2)  # Give a moment for final logs
                        break
                except queue.Empty:
                    pass
                
                time.sleep(0.5)
            
            # Cleanup
            if self.current_process and self.current_process.poll() is None:
                print("🛑 Stopping viam-server...")
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
            
            print(f"✅ Log capture complete: {log_file}")
            return log_file, video_finished
            
        except Exception as e:
            print(f"❌ Error running viam-server: {e}")
            if self.current_process:
                self.current_process.kill()
            return None, False
    
    def _monitor_logs(self, stdout, log_file):
        """Monitor stdout and write to log file while watching for end-of-file signal."""
        try:
            with open(log_file, 'w') as f:
                for line in stdout:
                    f.write(line)
                    f.flush()
                    
                    # Check for end-of-file signal
                    if "End of file" in line and "stopping playback" in line:
                        self.log_queue.put(line)
                    
                    # Also capture other important signals
                    if any(signal in line for signal in [
                        "🎬 ===== MOTION DETECTED =====", 
                        "✅ Action ACCEPTED", 
                        "❌ Action REJECTED",
                        "⏱️  Analysis Duration"
                    ]):
                        # Print important events to console
                        if "Action ACCEPTED" in line or "Action REJECTED" in line:
                            print(f"📊 {line.strip()}")
        except Exception as e:
            print(f"❌ Log monitoring error: {e}")
    
    def run_analysis(self, log_file, video_name):
        """Run the classification analysis on the captured logs."""
        print(f"\n🔍 Running analysis for: {video_name}")
        
        try:
            # Run the extraction and analysis script
            cmd = ["python3", "extract_and_align_classifier.py", str(log_file)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Analysis completed successfully")
                
                # Save analysis output
                analysis_file = log_file.with_suffix('.analysis.txt')
                with open(analysis_file, 'w') as f:
                    f.write(f"Analysis for: {video_name}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(result.stdout)
                    if result.stderr:
                        f.write("\n" + "=" * 60 + "\n")
                        f.write("STDERR:\n")
                        f.write(result.stderr)
                
                print(f"📄 Analysis saved to: {analysis_file}")
                return analysis_file, result.stdout
            else:
                print(f"❌ Analysis failed (exit code: {result.returncode})")
                print(f"Error: {result.stderr}")
                return None, None
                
        except subprocess.TimeoutExpired:
            print("❌ Analysis timed out")
            return None, None
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return None, None
    
    def extract_summary_metrics(self, analysis_output):
        """Extract key metrics from analysis output."""
        if not analysis_output:
            return {}
        
        metrics = {}
        lines = analysis_output.split('\n')
        
        for line in lines:
            line = line.strip()
            if "Total detections:" in line:
                metrics['total_detections'] = int(line.split(':')[-1].strip())
            elif "Accepted detections:" in line:
                metrics['accepted_detections'] = int(line.split(':')[-1].strip())
            elif "Rejected detections:" in line:
                metrics['rejected_detections'] = int(line.split(':')[-1].strip())
            elif "Average confidence:" in line:
                try:
                    metrics['avg_confidence'] = float(line.split(':')[-1].strip().replace('%', ''))
                except:
                    pass
            elif "Average similarity:" in line:
                try:
                    metrics['avg_similarity'] = float(line.split(':')[-1].strip().replace('%', ''))
                except:
                    pass
            elif "Average analysis time:" in line:
                try:
                    metrics['avg_analysis_time'] = float(line.split(':')[-1].strip().replace('s', ''))
                except:
                    pass
        
        return metrics
    
    async def run_evaluation(self):
        """Run the complete evaluation pipeline for all videos."""
        print("🎯 Starting Automated Evaluation Pipeline")
        print("=" * 60)
        print(f"📂 Videos to process: {len(self.videos)}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⚙️  Viam config: {self.viam_config_path}")
        print(f"🤖 Machine ID: {self.machine_id}")
        
        all_metrics = []
        
        for i, video_path in enumerate(self.videos, 1):
            print(f"\n{'='*60}")
            print(f"🎬 Processing Video {i}/{len(self.videos)}: {video_path.name}")
            print(f"{'='*60}")
            
            if not video_path.exists():
                print(f"❌ Video file not found: {video_path}")
                continue
            
            video_result = {
                'video': str(video_path),
                'name': video_path.name,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'metrics': {}
            }
            
            try:
                # Step 1: Update Viam machine config with new video path
                await self.update_video_path(video_path)
                
                # Step 2: Run viam-server and capture logs
                log_file, video_finished = self.run_viam_server(video_path)
                
                if log_file:
                    video_result['log_file'] = str(log_file)
                    video_result['video_completed'] = video_finished
                    
                    # Step 3: Run analysis
                    analysis_file, analysis_output = self.run_analysis(log_file, video_path.name)
                    
                    if analysis_file:
                        video_result['analysis_file'] = str(analysis_file)
                        video_result['metrics'] = self.extract_summary_metrics(analysis_output)
                        video_result['success'] = True
                        all_metrics.append(video_result['metrics'])
                        
                        print(f"✅ Successfully processed: {video_path.name}")
                    else:
                        print(f"❌ Analysis failed for: {video_path.name}")
                else:
                    print(f"❌ Log capture failed for: {video_path.name}")
                
                self.results['videos'].append(video_result)
                
            except Exception as e:
                print(f"❌ Error processing {video_path.name}: {e}")
                video_result['error'] = str(e)
                self.results['videos'].append(video_result)
        
        # Generate final summary
        self.generate_summary(all_metrics)
        self.save_results()
        
        print(f"\n🎉 Evaluation Pipeline Complete!")
        print(f"📊 Results saved to: {self.output_dir}")
    
    def generate_summary(self, all_metrics):
        """Generate summary statistics across all videos."""
        print(f"\n📊 Generating Summary Report")
        print("=" * 60)
        
        if not all_metrics:
            print("❌ No successful analyses to summarize")
            return
        
        # Calculate aggregate statistics
        summary = {
            'total_videos': len(self.videos),
            'successful_analyses': len(all_metrics),
            'total_detections': sum(m.get('total_detections', 0) for m in all_metrics),
            'total_accepted': sum(m.get('accepted_detections', 0) for m in all_metrics),
            'total_rejected': sum(m.get('rejected_detections', 0) for m in all_metrics),
        }
        
        # Calculate averages
        if all_metrics:
            summary['avg_detections_per_video'] = summary['total_detections'] / len(all_metrics)
            summary['overall_acceptance_rate'] = (summary['total_accepted'] / summary['total_detections'] * 100) if summary['total_detections'] > 0 else 0
            
            confidences = [m.get('avg_confidence') for m in all_metrics if m.get('avg_confidence')]
            if confidences:
                summary['avg_confidence_across_videos'] = sum(confidences) / len(confidences)
            
            similarities = [m.get('avg_similarity') for m in all_metrics if m.get('avg_similarity')]
            if similarities:
                summary['avg_similarity_across_videos'] = sum(similarities) / len(similarities)
            
            times = [m.get('avg_analysis_time') for m in all_metrics if m.get('avg_analysis_time')]
            if times:
                summary['avg_analysis_time_across_videos'] = sum(times) / len(times)
        
        self.results['summary'] = summary
        
        # Print summary
        print(f"📹 Videos processed: {summary['successful_analyses']}/{summary['total_videos']}")
        print(f"🎯 Total detections: {summary['total_detections']}")
        print(f"✅ Accepted: {summary['total_accepted']}")
        print(f"❌ Rejected: {summary['total_rejected']}")
        if summary.get('overall_acceptance_rate'):
            print(f"📈 Overall acceptance rate: {summary['overall_acceptance_rate']:.1f}%")
        if summary.get('avg_confidence_across_videos'):
            print(f"🎯 Average confidence: {summary['avg_confidence_across_videos']:.1f}%")
        if summary.get('avg_similarity_across_videos'):
            print(f"📊 Average similarity: {summary['avg_similarity_across_videos']:.1f}%")
        if summary.get('avg_analysis_time_across_videos'):
            print(f"⚡ Average analysis time: {summary['avg_analysis_time_across_videos']:.1f}s")
    
    def save_results(self):
        """Save complete results to JSON file."""
        results_file = self.output_dir / f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"💾 Complete results saved to: {results_file}")
    
    async def cleanup(self):
        """Restore original machine configuration."""
        if self.original_machine_config:
            print("🔄 Restoring original machine config...")
            try:
                await self.update_machine_config(self.original_machine_config)
                print("✅ Original machine config restored")
            except Exception as e:
                print(f"❌ Failed to restore original config: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Automated Viam Action Classifier Evaluation")
    
    # Video input options
    video_group = parser.add_mutually_exclusive_group(required=True)
    video_group.add_argument('--videos', nargs='+', help='List of video files to process')
    video_group.add_argument('--video-dir', help='Directory containing video files')
    
    # Configuration options
    parser.add_argument('--config', 
                       default='/Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json',
                       help='Path to Viam configuration file')
    parser.add_argument('--machine-id',
                       help='Viam machine ID (if not in config file)')
    parser.add_argument('--output-dir', 
                       default='evaluation_results',
                       help='Output directory for results')
    parser.add_argument('--timeout', 
                       type=int, 
                       default=10,
                       help='Timeout per video in minutes')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine video files
    if args.videos:
        video_files = args.videos
    else:
        video_dir = Path(args.video_dir)
        if not video_dir.exists():
            print(f"❌ Video directory not found: {video_dir}")
            sys.exit(1)
        
        # Find all video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(video_dir.glob(f'*{ext}'))
        
        if not video_files:
            print(f"❌ No video files found in: {video_dir}")
            sys.exit(1)
    
    print(f"🎬 Found {len(video_files)} videos to process")
    for video in video_files:
        print(f"   📹 {Path(video).name}")
    
    # Create and run pipeline
    pipeline = EvaluationPipeline(args.config, video_files, args.output_dir, args.machine_id)
    
    try:
        await pipeline.run_evaluation()
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await pipeline.cleanup()

def run_main():
    """Wrapper to run the async main function."""
    asyncio.run(main())

if __name__ == "__main__":
    run_main() 