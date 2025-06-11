#!/usr/bin/env python3
"""
Simplified Automated Evaluation Pipeline for Viam Action Classifier

This script simplifies the evaluation process:
1. Assumes video path is manually configured in Viam dashboard
2. Runs viam-server and captures logs
3. Detects when video playback completes
4. Runs classification analysis on captured logs

Usage:
    python automate_evaluation.py [--config config.json] [--output-dir results] [--timeout 10]
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

class EvaluationPipeline:
    def __init__(self, viam_config_path, output_dir="evaluation_results", timeout_minutes=10):
        self.viam_config_path = Path(viam_config_path)
        self.base_output_dir = Path(output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        self.timeout_minutes = timeout_minutes
        
        # Create unique subdirectory for this evaluation run
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = self.base_output_dir / f"run_{self.run_timestamp}"
        self.output_dir.mkdir(exist_ok=True)
        
        self.current_process = None
        self.log_queue = queue.Queue()
        
        # Results tracking
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'run_id': self.run_timestamp,
            'output_directory': str(self.output_dir),
            'timeout_minutes': timeout_minutes,
            'summary': {}
        }
    
    def run_viam_server(self, timeout_minutes=None):
        """Run viam-server and capture logs until video finishes or timeout."""
        # Use instance timeout if not specified
        if timeout_minutes is None:
            timeout_minutes = self.timeout_minutes
            
        print(f"🚀 Starting viam-server")
        print(f"⏱️  Timeout: {timeout_minutes} minutes")
        print(f"📁 Run directory: {self.output_dir}")
        
        # Prepare log file in run-specific directory
        log_file = self.output_dir / f"viam_server_{self.run_timestamp}.log"
        
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
                        "Motion detected", 
                        "Action ACCEPTED", 
                        "Action REJECTED",
                        "Analysis Duration"
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
            # Change to evaluation directory to run the analysis script
            original_cwd = os.getcwd()
            script_dir = Path(__file__).parent
            os.chdir(script_dir)
            
            # Run the extraction and analysis script
            cmd = ["python3", "extract_and_align_classifier.py", str(log_file)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Return to original directory
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                print("✅ Analysis completed successfully")
                
                # Save analysis output in run-specific directory
                analysis_file = self.output_dir / f"analysis_{self.run_timestamp}.txt"
                with open(analysis_file, 'w') as f:
                    f.write(f"Analysis for: {video_name}\n")
                    f.write(f"Run ID: {self.run_timestamp}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(result.stdout)
                    if result.stderr:
                        f.write("\n" + "=" * 60 + "\n")
                        f.write("STDERR:\n")
                        f.write(result.stderr)
                
                # Also check if timeline log was generated and move it to run directory
                timeline_pattern = f"*{self.run_timestamp}*timeline.log"
                for timeline_file in script_dir.glob(timeline_pattern):
                    dest_file = self.output_dir / timeline_file.name
                    shutil.move(str(timeline_file), str(dest_file))
                    print(f"📄 Timeline log moved to: {dest_file}")
                
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
    
    def run_evaluation(self):
        """Run the simplified evaluation pipeline for a single session."""
        print("🎯 Starting Simplified Evaluation Pipeline")
        print("=" * 60)
        print(f"📁 Base output directory: {self.base_output_dir}")
        print(f"📁 Run output directory: {self.output_dir}")
        print(f"🆔 Run ID: {self.run_timestamp}")
        print(f"⏱️  Timeout setting: {self.timeout_minutes} minutes")
        print(f"⚙️  Viam config: {self.viam_config_path}")
        print("📋 Make sure your video is configured in the Viam dashboard")
        
        # Create a README file in the run directory
        readme_file = self.output_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(f"# Evaluation Run: {self.run_timestamp}\n\n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}\n")
            f.write(f"**Timeout:** {self.timeout_minutes} minutes\n")
            f.write(f"**Viam Config:** {self.viam_config_path}\n\n")
            f.write("## Files in this directory:\n")
            f.write("- `viam_server_*.log` - Raw server logs\n")
            f.write("- `analysis_*.txt` - Classification analysis results\n")
            f.write("- `*_timeline.log` - Processed detection timeline\n")
            f.write("- `evaluation_results_*.json` - Complete evaluation metrics\n")
            f.write("- `README.md` - This file\n")
        
        # Step 1: Run viam-server and capture logs (use instance timeout)
        log_file, video_finished = self.run_viam_server()
        
        if log_file:
            video_result = {
                'log_file': str(log_file.relative_to(self.base_output_dir)),
                'video_completed': video_finished,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'metrics': {}
            }
            
            # Step 2: Run analysis
            analysis_file, analysis_output = self.run_analysis(log_file, "current_session")
            
            if analysis_file:
                video_result['analysis_file'] = str(analysis_file.relative_to(self.base_output_dir))
                video_result['metrics'] = self.extract_summary_metrics(analysis_output)
                video_result['success'] = True
                
                print(f"✅ Successfully processed session")
                
                # Generate summary
                self.generate_summary([video_result['metrics']])
                self.results['session'] = video_result
            else:
                print(f"❌ Analysis failed")
                self.results['session'] = video_result
        else:
            print(f"❌ Log capture failed")
        
        self.save_results()
        print(f"\n🎉 Evaluation Pipeline Complete!")
        print(f"📊 Results saved to: {self.output_dir}")
        print(f"🔗 Run directory: {self.output_dir}")
    
    def generate_summary(self, all_metrics):
        """Generate summary statistics for the session."""
        print(f"\n📊 Generating Summary Report")
        print("=" * 60)
        
        if not all_metrics:
            print("❌ No successful analyses to summarize")
            return
        
        metrics = all_metrics[0]  # Single session
        
        # Calculate statistics
        summary = {
            'total_detections': metrics.get('total_detections', 0),
            'accepted_detections': metrics.get('accepted_detections', 0),
            'rejected_detections': metrics.get('rejected_detections', 0),
        }
        
        # Calculate acceptance rate
        if summary['total_detections'] > 0:
            summary['acceptance_rate'] = (summary['accepted_detections'] / summary['total_detections'] * 100)
        else:
            summary['acceptance_rate'] = 0
        
        # Add other metrics
        if metrics.get('avg_confidence'):
            summary['avg_confidence'] = metrics['avg_confidence']
        if metrics.get('avg_similarity'):
            summary['avg_similarity'] = metrics['avg_similarity']
        if metrics.get('avg_analysis_time'):
            summary['avg_analysis_time'] = metrics['avg_analysis_time']
        
        self.results['summary'] = summary
        
        # Print summary
        print(f"🎯 Total detections: {summary['total_detections']}")
        print(f"✅ Accepted: {summary['accepted_detections']}")
        print(f"❌ Rejected: {summary['rejected_detections']}")
        if summary.get('acceptance_rate'):
            print(f"📈 Acceptance rate: {summary['acceptance_rate']:.1f}%")
        if summary.get('avg_confidence'):
            print(f"🎯 Average confidence: {summary['avg_confidence']:.1f}%")
        if summary.get('avg_similarity'):
            print(f"📊 Average similarity: {summary['avg_similarity']:.1f}%")
        if summary.get('avg_analysis_time'):
            print(f"⚡ Average analysis time: {summary['avg_analysis_time']:.1f}s")
    
    def save_results(self):
        """Save complete results to JSON file in run-specific directory."""
        results_file = self.output_dir / f"evaluation_results_{self.run_timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"💾 Complete results saved to: {results_file}")
        
        # Also create a summary file for quick reference
        summary_file = self.output_dir / f"summary_{self.run_timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Evaluation Run Summary: {self.run_timestamp}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Timestamp: {self.results['timestamp']}\n")
            f.write(f"Run ID: {self.run_timestamp}\n\n")
            
            if 'summary' in self.results:
                summary = self.results['summary']
                f.write("Performance Metrics:\n")
                f.write(f"- Total detections: {summary.get('total_detections', 0)}\n")
                f.write(f"- Accepted: {summary.get('accepted_detections', 0)}\n")
                f.write(f"- Rejected: {summary.get('rejected_detections', 0)}\n")
                if summary.get('acceptance_rate'):
                    f.write(f"- Acceptance rate: {summary['acceptance_rate']:.1f}%\n")
                if summary.get('avg_confidence'):
                    f.write(f"- Average confidence: {summary['avg_confidence']:.1f}%\n")
                if summary.get('avg_similarity'):
                    f.write(f"- Average similarity: {summary['avg_similarity']:.1f}%\n")
                if summary.get('avg_analysis_time'):
                    f.write(f"- Average analysis time: {summary['avg_analysis_time']:.1f}s\n")
        
        print(f"📋 Quick summary saved to: {summary_file}")
    
    def cleanup(self):
        """Restore original configuration."""
        pass

def main():
    parser = argparse.ArgumentParser(description="Automated Viam Action Classifier Evaluation")
    
    # Configuration options
    parser.add_argument('--config', 
                       default='/Users/marcuslam/Desktop/Gambit/viam-marcus-dev-main.json',
                       help='Path to Viam configuration file')
    parser.add_argument('--output-dir', 
                       default='evaluation_results',
                       help='Output directory for results')
    parser.add_argument('--timeout', 
                       type=int, 
                       default=10,
                       help='Timeout per video in minutes (default: 10)')
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"🔧 Configuration:")
    print(f"   Config file: {args.config}")
    print(f"   Output directory: {args.output_dir}")
    print(f"   Timeout: {args.timeout} minutes")
    print()
    
    # Create and run pipeline with custom timeout
    pipeline = EvaluationPipeline(args.config, args.output_dir, args.timeout)
    
    try:
        pipeline.run_evaluation()
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
    finally:
        pipeline.cleanup()

if __name__ == "__main__":
    main() 