#!/usr/bin/env python3
"""
Interactive Viam camera recording with cooking action coaching.
Guides users through a series of cooking actions while recording video.
Stop with Ctrl‑C.
"""

import asyncio, os, signal, cv2, numpy as np, sys, csv, time
from datetime import datetime
from viam.robot.client import RobotClient
from viam.rpc.dial import DialOptions
from viam.components.camera import Camera
from viam.media.video import CameraMimeType

# ---------------------------------------------------------------------
# Config – change only these four lines
CAMERA_NAME = "overhead-rgb"   # the name in your Viam config
FPS         = 10               # playback + capture rate
OUT_FILE    = "cooking_actions_recording.mp4"
LOG_FILE    = "cooking_actions_log.csv"
# ---------------------------------------------------------------------

class ActionLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.start_time = None
        self.current_action = None
        self.action_start_time = None
        self.rep_number = 0
        self.session_start = None
        
        # Initialize CSV file with headers
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'session_timestamp',
                'action_category', 
                'action_description',
                'repetition_number',
                'start_time_seconds',
                'end_time_seconds',
                'duration_seconds',
                'video_filename',
                'notes'
            ])
        
        print(f"📋 Action log will be saved to: {self.log_file}")
    
    def start_session(self):
        """Mark the start of the recording session."""
        self.session_start = time.time()
        self.start_time = self.session_start
        session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log session start
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                session_time,
                'session',
                'Recording session started',
                0,
                0.0,
                0.0,
                0.0,
                OUT_FILE,
                'Session initialization'
            ])
    
    def start_action(self, action_category, action_description, rep_number):
        """Log the start of an action."""
        self.current_action = action_description
        self.action_start_time = time.time()
        self.rep_number = rep_number
        
        elapsed = self.action_start_time - self.start_time
        print(f"📝 Logging action start: {action_description} (Rep {rep_number}) at {elapsed:.1f}s")
    
    def end_action(self, notes=""):
        """Log the end of an action."""
        if self.action_start_time is None:
            return
            
        end_time = time.time()
        start_elapsed = self.action_start_time - self.start_time
        end_elapsed = end_time - self.start_time
        duration = end_time - self.action_start_time
        
        session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine action category from description
        action_category = "unknown"
        if "pan" in self.current_action.lower():
            action_category = "pan_manipulation"
        elif "lid" in self.current_action.lower():
            action_category = "lid_manipulation"
        elif "food" in self.current_action.lower() and ("stir" in self.current_action.lower() or "flip" in self.current_action.lower()):
            action_category = "food_cooking"
        elif "food" in self.current_action.lower():
            action_category = "food_manipulation"
        
        # Write to CSV
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                session_time,
                action_category,
                self.current_action,
                self.rep_number,
                f"{start_elapsed:.2f}",
                f"{end_elapsed:.2f}",
                f"{duration:.2f}",
                OUT_FILE,
                notes
            ])
        
        print(f"✅ Action logged: {duration:.1f}s duration")
        
        # Reset
        self.current_action = None
        self.action_start_time = None
    
    def log_phase_change(self, phase_name, notes=""):
        """Log phase transitions (setup, coaching, free practice)."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                session_time,
                'phase_transition',
                phase_name,
                0,
                f"{elapsed:.2f}",
                f"{elapsed:.2f}",
                0.0,
                OUT_FILE,
                notes
            ])

class CookingCoach:
    def __init__(self, logger):
        self.current_step = 0
        self.total_steps = 0
        self.setup_complete = False
        self.recording_active = False
        self.logger = logger
        
    async def get_user_input(self, prompt):
        """Get user input asynchronously."""
        print(f"\n🎬 {prompt}")
        print("Press ENTER to continue...")
        
        # Use asyncio to handle input without blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input)
        
    async def setup_phase(self):
        """Initial setup and preparation phase."""
        print("\n" + "="*60)
        print("🍳 COOKING ACTION RECORDING SETUP")
        print("="*60)
        
        await self.get_user_input(
            "Welcome! We'll record you performing cooking actions.\n"
            "Please prepare the following items:\n"
            "• A pan\n"
            "• A lid that fits the pan\n"
            "• Food of your choice (apple, toy food, or real ingredients)\n\n"
            "IMPORTANT: Tell me now - does your recipe involve STIRRING or FLIPPING?"
        )
        
        # Get cooking method
        print("\nType 'stir' for stirring actions or 'flip' for flipping actions:")
        loop = asyncio.get_event_loop()
        cooking_method = await loop.run_in_executor(None, input)
        self.cooking_method = cooking_method.strip().lower()
        
        if self.cooking_method not in ['stir', 'flip']:
            self.cooking_method = 'stir'  # Default to stirring
            
        action_word = "stirring" if self.cooking_method == 'stir' else "flipping"
        
        await self.get_user_input(
            f"Perfect! I'll guide you through {action_word} actions.\n"
            "Make sure your workspace is ready and all items are within reach.\n"
            "The camera should have a clear view of your cooking area."
        )
        
        self.setup_complete = True
        
    async def execute_action_sequence(self, action_name, count=3, delay=5):
        """Execute a sequence of actions with delays."""
        print(f"\n{'='*50}")
        print(f"🎯 STARTING: {action_name.upper()}")
        print(f"{'='*50}")
        
        for i in range(count):
            # Log action start
            self.logger.start_action(
                action_category="cooking_action",
                action_description=action_name,
                rep_number=i+1
            )
            
            await self.get_user_input(
                f"Step {i+1}/{count}: {action_name}\n"
                f"Get ready to perform this action..."
            )
            
            # Log action end
            self.logger.end_action(f"Repetition {i+1} of {count}")
            
            if i < count - 1:  # Don't wait after the last action
                print(f"⏳ Waiting {delay} seconds before next action...")
                await asyncio.sleep(delay)
                
    async def run_coaching_sequence(self):
        """Run the complete coaching sequence."""
        if not self.setup_complete:
            await self.setup_phase()
            
        # Log coaching phase start
        self.logger.log_phase_change("Coaching sequence started", "Beginning guided actions")
        
        print(f"\n🚀 STARTING RECORDING SESSION")
        print("The camera is now recording all your actions!")
        
        # Sequence of cooking actions
        actions = [
            ("Add the pan to the cooking area, then remove it", 3),
            ("Place the lid on the pan area, then remove it", 3),
            (f"Add the food, then perform a {self.cooking_method} motion", 3),
            ("Add the food to the pan, then remove it completely", 3)
        ]
        
        self.total_steps = sum(count for _, count in actions)
        
        for action_desc, count in actions:
            await self.execute_action_sequence(action_desc, count)
            
        # Log coaching completion
        self.logger.log_phase_change("Coaching sequence completed", "All guided actions finished")
        
        print(f"\n🎉 EXCELLENT! All cooking actions completed!")
        print("Recording will continue until you press Ctrl-C")
        print("Feel free to practice more or try variations!")
        
        # Log free practice phase
        self.logger.log_phase_change("Free practice started", "User can practice freely")

async def connect() -> RobotClient:
    """Connect to the robot via the Viam Cloud."""
    print("🔌 Attempting to connect to Viam robot...")
    print(f"   Address: {os.environ.get('VIAM_ADDRESS', 'NOT SET')}")
    print(f"   API Key ID: {os.environ.get('VIAM_API_KEY_ID', 'NOT SET')[:20]}...")
    
    try:
        opts = RobotClient.Options(
            dial_options=DialOptions.with_api_key(
                api_key_id=os.environ["VIAM_API_KEY_ID"],
                api_key=os.environ["VIAM_API_KEY"]
            ),
            disable_webrtc=True        # headless client – no SDP exchange
        )
        
        robot = await RobotClient.at_address(os.environ["VIAM_ADDRESS"], opts)
        
        # Test connection by getting robot status
        print("✅ Successfully connected to Viam robot!")
        
        # Get basic robot info
        try:
            resource_names = await robot.get_status()
            print(f"📋 Robot status retrieved - {len(resource_names)} resources found")
        except Exception as e:
            print(f"⚠️  Warning: Could not get robot status: {e}")
            
        return robot
        
    except KeyError as e:
        print(f"❌ Missing environment variable: {e}")
        print("Make sure to set VIAM_API_KEY_ID, VIAM_API_KEY, and VIAM_ADDRESS")
        raise
    except Exception as e:
        print(f"❌ Failed to connect to robot: {e}")
        print("Check your credentials and robot status at app.viam.com")
        raise

async def record_video(coach, logger):
    """Handle video recording while coaching runs."""
    robot = await connect()
    
    print(f"📷 Attempting to connect to camera: '{CAMERA_NAME}'")
    try:
        cam = Camera.from_robot(robot, CAMERA_NAME)
        print("✅ Successfully connected to camera!")
    except Exception as e:
        print(f"❌ Failed to connect to camera '{CAMERA_NAME}': {e}")
        print("Available cameras might be listed differently in your Viam config")
        await robot.close()
        raise

    # Get first frame to discover resolution
    print("🖼️  Getting first frame to determine video resolution...")
    try:
        viam_img = await cam.get_image(CameraMimeType.JPEG)
        frame = cv2.imdecode(np.frombuffer(viam_img, np.uint8), cv2.IMREAD_COLOR)
        h, w = frame.shape[:2]
        print(f"📐 Video resolution detected: {w}x{h}")
    except Exception as e:
        print(f"❌ Failed to get first frame: {e}")
        await robot.close()
        raise
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUT_FILE, fourcc, FPS, (w, h))
    
    if not writer.isOpened():
        print(f"❌ Failed to create video writer for {OUT_FILE}")
        await robot.close()
        raise RuntimeError("Could not create video file")

    print(f"🎥 Interactive recording started!")
    print(f"   Camera: {CAMERA_NAME}")
    print(f"   Output: {OUT_FILE}")
    print(f"   Log: {LOG_FILE}")
    print(f"   Resolution: {w}x{h}")
    print(f"   FPS: {FPS}")
    
    # Start session logging
    logger.start_session()
    coach.recording_active = True

    # Graceful Ctrl‑C handling
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    frame_count = 0
    try:
        while not stop.is_set():
            try:
                viam_img = await cam.get_image(CameraMimeType.JPEG)
                frame = cv2.imdecode(np.frombuffer(viam_img, np.uint8), cv2.IMREAD_COLOR)
                writer.write(frame)
                frame_count += 1
                
                # Progress indicator every 200 frames (less frequent during interactive mode)
                if frame_count % 200 == 0:
                    duration = frame_count / FPS
                    print(f"📊 Recording progress: {frame_count} frames ({duration:.1f} seconds)")
                    
            except Exception as e:
                print(f"⚠️  Warning: Frame capture error: {e}")
                await asyncio.sleep(0.1)  # Brief pause before retrying
                
            await asyncio.sleep(1 / FPS)
    finally:
        writer.release()
        await robot.close()
        coach.recording_active = False
        duration = frame_count / FPS
        
        # Log session end
        logger.log_phase_change("Recording session ended", f"Total duration: {duration:.1f}s, Frames: {frame_count}")
        
        print(f"\n✅ Interactive recording completed!")
        print(f"   Total frames: {frame_count}")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Video saved to: {OUT_FILE}")
        print(f"   Action log saved to: {LOG_FILE}")

async def main():
    """Main function that runs coaching and recording concurrently."""
    # Initialize logger
    logger = ActionLogger(LOG_FILE)
    coach = CookingCoach(logger)
    
    # Run setup first, then start recording and coaching in parallel
    await coach.setup_phase()
    
    # Start both recording and coaching concurrently
    recording_task = asyncio.create_task(record_video(coach, logger))
    coaching_task = asyncio.create_task(coach.run_coaching_sequence())
    
    try:
        # Wait for either task to complete (recording continues until Ctrl-C)
        await asyncio.gather(recording_task, coaching_task, return_exceptions=True)
    except KeyboardInterrupt:
        print(f"\n🛑 Recording stopped by user")
    finally:
        # Clean up
        if not recording_task.done():
            recording_task.cancel()
        if not coaching_task.done():
            coaching_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 Session ended. Check your files:")
        print(f"   Video: {OUT_FILE}")
        print(f"   Action log: {LOG_FILE}")
        sys.exit(0) 