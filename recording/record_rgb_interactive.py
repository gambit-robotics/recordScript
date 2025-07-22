#!/usr/bin/env python3
"""
Interactive Viam camera recording with cooking action coaching.
Guides users through a series of cooking actions while recording separate videos for each action type.
Stop with Ctrl-C.
"""

import asyncio, os, signal, cv2, numpy as np, sys, csv, time, argparse
from datetime import datetime
from dotenv import load_dotenv
from viam.robot.client import RobotClient
from viam.rpc.dial import DialOptions
from viam.components.camera import Camera
from viam.media.video import CameraMimeType

# Load environment variables from .env file
# Try multiple locations for .env file
env_paths = [
    ".env",  # Current directory
    "../.env",  # Parent directory
    "../../.env",  # Two levels up
    os.path.join(os.path.dirname(__file__), ".env"),  # Same directory as script
    os.path.join(os.path.dirname(__file__), "..", ".env"),  # Parent of script directory
]

env_loaded = False
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        print(f"✅ Loaded environment from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("⚠️  No .env file found. Using default environment variables.")
    print("💡 Create a .env file in the project root with your Viam credentials:")
    print("   VIAM_API_KEY_ID=your_api_key_id")
    print("   VIAM_API_KEY=your_api_key")
    print("   VIAM_ADDRESS=your_robot_address")
    print("   VIAM_CAMERA_NAME=your_camera_name")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Interactive Viam camera recording with cooking action coaching')
parser.add_argument('--output-dir', '-o', default='output', 
                   help='Directory to save ground truth CSV file (default: output directory)')
args = parser.parse_args()

# Ensure output directory exists
os.makedirs(args.output_dir, exist_ok=True)

# ---------------------------------------------------------------------
# Config – change only these four lines
CAMERA_NAME = os.environ.get("VIAM_CAMERA_NAME", "overhead-rgb")  # Camera name from Viam config
FPS         = 10               # playback + capture rate
OUT_FILE_PREFIX = "cooking_actions"  # Prefix for video files
LOG_FILE    = os.path.join(args.output_dir, "cooking_actions_log.csv")
GT_FILE     = os.path.join(args.output_dir, "cooking_actions_ground_truth.csv")
SHOW_LIVE_FEED = True          # Display live camera feed window
# ---------------------------------------------------------------------

class ActionLogger:
    def __init__(self, log_file, gt_file):
        self.log_file = log_file
        self.gt_file = gt_file
        self.start_time = None
        self.current_action = None
        self.action_start_time = None
        self.rep_number = 0
        self.session_start = None
        self.current_sequence = None
        self.sequence_start_time = None
        
        # Initialize detailed log CSV file with headers
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'session_timestamp',
                'action_sequence',
                'action_category', 
                'action_description',
                'repetition_number',
                'start_time_seconds',
                'end_time_seconds',
                'duration_seconds',
                'video_filename',
                'notes'
            ])
        
        # Initialize ground truth CSV file with headers
        with open(self.gt_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'video_filename',
                'category_label',
                'action_label',
                'start_time_seconds',
                'end_time_seconds',
                'duration_seconds',
                'video_start_frame',
                'video_end_frame'
            ])
        
        print(f"📋 Detailed action log will be saved to: {self.log_file}")
        print(f"📋 Ground truth file will be saved to: {self.gt_file}")
    
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
                'session',
                'Recording session started',
                0,
                0.0,
                0.0,
                0.0,
                'multiple_files',
                'Session initialization'
            ])
    
    def start_sequence(self, sequence_name, video_filename):
        """Mark the start of a new action sequence."""
        self.current_sequence = sequence_name
        self.sequence_start_time = time.time()
        elapsed = self.sequence_start_time - self.start_time
        session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"🎬 Starting sequence: {sequence_name} -> {video_filename}")
        
        # Log sequence start
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                session_time,
                sequence_name,
                'sequence_start',
                f'Starting {sequence_name}',
                0,
                f"{elapsed:.2f}",
                f"{elapsed:.2f}",
                0.0,
                video_filename,
                f'Sequence started at {elapsed:.1f}s'
            ])
    
    def end_sequence(self, notes=""):
        """Mark the end of the current action sequence."""
        if self.sequence_start_time is None:
            return
            
        end_time = time.time()
        start_elapsed = self.sequence_start_time - self.start_time
        end_elapsed = end_time - self.start_time
        duration = end_time - self.sequence_start_time
        session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"🏁 Ending sequence: {self.current_sequence} (Duration: {duration:.1f}s)")
        
        # Log sequence end
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                session_time,
                self.current_sequence,
                'sequence_end',
                f'Completed {self.current_sequence}',
                0,
                f"{start_elapsed:.2f}",
                f"{end_elapsed:.2f}",
                f"{duration:.2f}",
                'sequence_completed',
                f'Sequence duration: {duration:.1f}s'
            ])
        
        # Reset sequence tracking
        self.current_sequence = None
        self.sequence_start_time = None
    
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
        action_lower = self.current_action.lower()
        
        if "pan" in action_lower:
            action_category = "pan_manipulation"
        elif "lid" in action_lower:
            action_category = "lid_manipulation"
        elif action_lower in ["stir", "flip"]:
            action_category = "food_cooking"
        elif "food" in action_lower:
            action_category = "food_manipulation"
        elif action_lower == "season":
            action_category = "food_seasoning"
        
        # Get current video filename
        current_video = os.path.join(args.output_dir, f"{OUT_FILE_PREFIX}_{self.current_sequence.lower().replace(' ', '_')}.mp4") if self.current_sequence else "unknown.mp4"
        
        # Write to detailed log CSV
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                session_time,
                self.current_sequence or 'unknown',
                action_category,
                self.current_action,
                self.rep_number,
                f"{start_elapsed:.2f}",
                f"{end_elapsed:.2f}",
                f"{duration:.2f}",
                current_video,
                notes
            ])
        
        # Write to ground truth CSV (only for actual actions, not setup/phase changes)
        if self.current_action and self.current_action not in ['session', 'phase_transition']:
            # Calculate frame numbers based on FPS
            start_frame = int(start_elapsed * FPS)
            end_frame = int(end_elapsed * FPS)
            
            with open(self.gt_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    current_video,
                    action_category,
                    self.current_action,
                    f"{start_elapsed:.2f}",
                    f"{end_elapsed:.2f}",
                    f"{duration:.2f}",
                    start_frame,
                    end_frame
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
                'phase_transition',
                phase_name,
                0,
                f"{elapsed:.2f}",
                f"{elapsed:.2f}",
                0.0,
                'phase_change',
                notes
            ])

class CookingCoach:
    def __init__(self, logger):
        self.current_step = 0
        self.total_steps = 0
        self.setup_complete = False
        self.recording_active = False
        self.logger = logger
        self.current_action_text = "Waiting for next action..."
        self.current_rep = 0
        self.sequence_change_event = asyncio.Event()
        self.current_sequence_name = None
        self.sequence_active = False
        
    async def get_user_input(self, prompt):
        """Get user input asynchronously."""
        print(f"\n🎬 {prompt}")
        print("\n" + "⏭️  Press ENTER to continue..." + " " * 20)
        print("👆 WAITING FOR YOUR INPUT ^^")
        
        # Use asyncio to handle input without blocking
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, input)
            print("✅ Input received, continuing...")
        except Exception as e:
            print(f"⚠️  Input error: {e}")
    
    async def signal_sequence_start(self, sequence_name):
        """Signal the start of a new action sequence."""
        self.current_sequence_name = sequence_name
        self.sequence_active = True
        self.sequence_change_event.set()
        # Wait a moment for video recorder to process
        await asyncio.sleep(1)
        
    async def signal_sequence_end(self):
        """Signal the end of the current action sequence."""
        self.sequence_active = False
        self.current_sequence_name = None
        self.sequence_change_event.set()
        # Wait a moment for video recorder to process
        await asyncio.sleep(1)
        
    async def setup_phase(self):
        """Initial setup and preparation phase."""
        print("\n" + "="*60)
        print("🍳 COOKING ACTION RECORDING SETUP")
        print("="*60)
        
        print("🔧 Step 1: Preparation")
        await self.get_user_input(
            "Welcome! We'll record you performing cooking actions.\n\n"
            "🚨 IMPORTANT: Make sure your cooktop/workspace is COMPLETELY EMPTY!\n"
            "   • No pan on the cooktop\n"
            "   • No food items visible\n"
            "   • Clean, clear workspace\n\n"
            "Please prepare the following items OFF to the side:\n"
            "• A pan\n"
            "• A lid that fits the pan\n"
            "• Food of your choice (apple, toy food, or real ingredients)\n\n"
            "We'll guide you to add/remove items step by step.\n"
            "Does your recipe involve STIRRING or FLIPPING?"
        )
        
        # Get cooking method
        print("\n🔧 Step 2: Cooking method")
        print("\nType 'stir' for stirring actions or 'flip' for flipping actions:")
        print("👆 WAITING FOR YOUR COOKING METHOD ^^")
        loop = asyncio.get_event_loop()
        try:
            cooking_method = await loop.run_in_executor(None, input)
            self.cooking_method = cooking_method.strip().lower()
            print(f"✅ Got cooking method: '{self.cooking_method}'")
        except Exception as e:
            print(f"⚠️  Input error: {e}, defaulting to 'stir'")
            self.cooking_method = 'stir'
        
        if self.cooking_method not in ['stir', 'flip']:
            print(f"⚠️  Invalid method '{self.cooking_method}', defaulting to 'stir'")
            self.cooking_method = 'stir'  # Default to stirring
            
        action_word = "stirring" if self.cooking_method == 'stir' else "flipping"
        
        print("\n🔧 Step 3: Final preparation")
        await self.get_user_input(
            f"Perfect! I'll guide you through {action_word} actions.\n\n"
            "✅ Confirm your workspace setup:\n"
            "   • Cooktop/workspace is completely empty\n"
            "   • Pan, lid, and food are ready off to the side\n"
            "   • Camera has a clear view of the cooking area\n\n"
            "🎥 Note: Each action type will be recorded as a separate video file:\n"
            "   • Pan manipulation exercises\n"
            "   • Lid manipulation exercises\n"
            f"   • Food {action_word} exercises\n"
            "   • Food manipulation exercises\n\n"
            "Ready to start recording!"
        )
        
        self.setup_complete = True
        print("🎉 Setup phase completed! Moving to recording...")
        
    async def execute_single_action(self, action_name, action_description, rep_info=""):
        """Execute a single action with user confirmation."""
        # Update status for live feed display (use full description for user)
        self.current_action_text = f"{action_name} {rep_info}"
        
        # Log action start (use simple description for data)
        self.logger.start_action(
            action_category="cooking_action",
            action_description=action_description,
            rep_number=self.current_rep
        )
        
        await self.get_user_input(
            f"{action_name}\n"
            f"Get ready to perform this action..."
        )
        
        # Log action end
        self.logger.end_action(f"{action_description} completed")
        
        # Wait 5 seconds between all actions
        self.current_action_text = f"Waiting 5 seconds..."
        print(f"⏳ Waiting 5 seconds...")
        await asyncio.sleep(5)
        
    async def execute_action_sequence(self, action_name, count=3, delay=5):
        """Execute a sequence of actions with delays."""
        print(f"\n{'='*50}")
        print(f"🎯 STARTING: {action_name.upper()}")
        print(f"{'='*50}")
        
        # Signal sequence start
        await self.signal_sequence_start(action_name)
        
        for i in range(count):
            self.current_rep = i + 1
            rep_info = f"(Rep {i+1}/{count})"
            
            if "pan" in action_name.lower():
                # Separate add and remove pan actions
                await self.execute_single_action(
                    "Add the pan to the cooking area", "add-pan", rep_info)
                await self.execute_single_action(
                    "Remove the pan from the cooking area", "remove-pan", rep_info)
                
            elif "lid" in action_name.lower():
                # Separate add and remove lid actions
                await self.execute_single_action(
                    "Place the lid on the pan area", "add-lid", rep_info)
                await self.execute_single_action(
                    "Remove the lid from the pan area", "remove-lid", rep_info)
                
            elif "food" in action_name.lower() and ("stir" in action_name.lower() or "flip" in action_name.lower()):
                # Food cooking actions
                await self.execute_single_action(
                    "Add the food to the cooking area", "add-food", rep_info)
                action_type = "stir" if self.cooking_method == "stir" else "flip"
                await self.execute_single_action(
                    f"Perform a {self.cooking_method} motion", action_type, rep_info)
                await self.execute_single_action(
                    "Remove the food from the cooking area", "remove-food", rep_info)
                
            elif "food" in action_name.lower():
                # Simple food add/remove
                await self.execute_single_action(
                    "Add the food to the pan area", "add-food", rep_info)
                await self.execute_single_action(
                    "Remove the food from the pan area", "remove-food", rep_info)
                
        self.current_action_text = "Action sequence completed"
        
        # Signal sequence end
        await self.signal_sequence_end()
                
    async def run_coaching_sequence(self):
        """Run the complete coaching sequence."""
        if not self.setup_complete:
            await self.setup_phase()
            
        # Log coaching phase start
        self.logger.log_phase_change("Coaching sequence started", "Beginning guided actions")
        
        print(f"\n🚀 STARTING RECORDING SESSION")
        print("The camera will record separate videos for each action type!")
        print("Remember: Start with an empty cooktop!")
        
        # Sequence of cooking actions
        actions = [
            ("Pan manipulation", 3),
            ("Lid manipulation", 3),  
            (f"Food cooking with {self.cooking_method}", 3),
            ("Food manipulation", 3)
        ]
        
        self.total_steps = sum(count for _, count in actions) * 2  # Each action now has 2+ steps
        
        for action_desc, count in actions:
            await self.execute_action_sequence(action_desc, count)
            
        # Log coaching completion
        self.logger.log_phase_change("Coaching sequence completed", "All guided actions finished")
        
        print(f"\n🎉 EXCELLENT! All cooking actions completed!")
        print("You can now review your separate video files!")
        print("Press Ctrl-C to end the session.")
        
        # Don't start free practice mode for separate videos
        self.current_action_text = "All sequences completed - Press Ctrl-C to finish"

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
            )
        )
        
        robot = await RobotClient.at_address(os.environ["VIAM_ADDRESS"], opts)
        
        # Test connection by getting robot status
        print("✅ Successfully connected to Viam robot!")
        
        # Get basic robot info
        try:
            resource_names = await robot.resource_names()
            print(f"📋 Robot status retrieved - {len(resource_names)} resources found")
        except Exception as e:
            print(f"⚠️  Warning: Could not get robot status: {e}")
            
        return robot
        
    except KeyError as e:
        print(f"❌ Missing environment variable: {e}")
        print("Make sure to set VIAM_API_KEY_ID, VIAM_API_KEY, and VIAM_ADDRESS")
        print("Either in your shell environment or in a .env file")
        raise
    except Exception as e:
        print(f"❌ Failed to connect to robot: {e}")
        print("Check your credentials and robot status at app.viam.com")
        raise

async def record_video(coach, logger):
    """Handle video recording with separate files for each action sequence."""
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
        frame = cv2.imdecode(np.frombuffer(viam_img.data, np.uint8), cv2.IMREAD_COLOR)
        h, w = frame.shape[:2]
        print(f"📐 Video resolution detected: {w}x{h}")
    except Exception as e:
        print(f"❌ Failed to get first frame: {e}")
        await robot.close()
        raise
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    
    # Video recording state
    current_writer = None
    current_video_file = None
    video_files_created = []
    
    print(f"🎥 Multi-file recording ready!")
    print(f"   Camera: {CAMERA_NAME}")
    print(f"   Output prefix: {OUT_FILE_PREFIX}")
    print(f"   Log: {LOG_FILE}")
    print(f"   Resolution: {w}x{h}")
    print(f"   FPS: {FPS}")
    print(f"   Live feed: {'Enabled' if SHOW_LIVE_FEED else 'Disabled'}")
    
    if SHOW_LIVE_FEED:
        print(f"📺 Live feed window opened. Press 'q' in the video window or Ctrl-C to stop.")
        cv2.namedWindow(f"Viam Camera: {CAMERA_NAME} (Multi-file)", cv2.WINDOW_AUTOSIZE)
    
    # Start session logging
    logger.start_session()
    coach.recording_active = True

    # Graceful Ctrl‑C handling
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    frame_count = 0
    sequence_frame_count = 0
    
    try:
        while not stop.is_set():
            # Check for sequence changes
            if coach.sequence_change_event.is_set():
                coach.sequence_change_event.clear()
                
                # Close current writer if exists
                if current_writer is not None:
                    current_writer.release()
                    if current_video_file:
                        duration = sequence_frame_count / FPS
                        print(f"✅ Completed video: {current_video_file} ({sequence_frame_count} frames, {duration:.1f}s)")
                        logger.end_sequence(f"Video saved: {current_video_file}")
                    current_writer = None
                    current_video_file = None
                    sequence_frame_count = 0
                
                # Start new writer if sequence is active
                if coach.sequence_active and coach.current_sequence_name:
                    # Create filename from sequence name
                    safe_name = coach.current_sequence_name.lower().replace(' ', '_').replace('/', '_')
                    current_video_file = os.path.join(args.output_dir, f"{OUT_FILE_PREFIX}_{safe_name}.mp4")
                    
                    current_writer = cv2.VideoWriter(current_video_file, fourcc, FPS, (w, h))
                    
                    if not current_writer.isOpened():
                        print(f"❌ Failed to create video writer for {current_video_file}")
                        current_writer = None
                        current_video_file = None
                    else:
                        video_files_created.append(current_video_file)
                        logger.start_sequence(coach.current_sequence_name, current_video_file)
                        print(f"🎬 Started recording: {current_video_file}")
            
            try:
                viam_img = await cam.get_image(CameraMimeType.JPEG)
                frame = cv2.imdecode(np.frombuffer(viam_img.data, np.uint8), cv2.IMREAD_COLOR)
                
                # Write to current video file if active
                if current_writer is not None:
                    current_writer.write(frame)
                    sequence_frame_count += 1
                
                frame_count += 1
                
                # Display live feed if enabled
                if SHOW_LIVE_FEED:
                    # Add coaching overlay
                    overlay_frame = frame.copy()
                    
                    # Recording indicator (different color for active/inactive)
                    if current_writer is not None:
                        cv2.circle(overlay_frame, (30, 30), 15, (0, 0, 255), -1)  # Red circle
                        cv2.putText(overlay_frame, "REC", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        cv2.circle(overlay_frame, (30, 30), 15, (0, 255, 255), -1)  # Yellow circle
                        cv2.putText(overlay_frame, "WAIT", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    
                    # Current action status (top center)
                    action_text = coach.current_action_text
                    text_size = cv2.getTextSize(action_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    text_x = (w - text_size[0]) // 2
                    cv2.rectangle(overlay_frame, (text_x - 10, 5), (text_x + text_size[0] + 10, 40), (0, 0, 0), -1)
                    cv2.putText(overlay_frame, action_text, (text_x, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    # Current video file name (top left, below REC indicator)
                    if current_video_file:
                        cv2.putText(overlay_frame, f"File: {current_video_file}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(overlay_frame, f"Frames: {sequence_frame_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    else:
                        cv2.putText(overlay_frame, "No active recording", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    
                    # Frame counter and time (bottom)
                    duration = frame_count / FPS
                    time_text = f"Total frames: {frame_count} | Time: {duration:.1f}s | Videos: {len(video_files_created)}"
                    cv2.putText(overlay_frame, time_text, (10, h-40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Instructions (bottom right)
                    instruction_text = "Press 'q' to stop"
                    cv2.putText(overlay_frame, instruction_text, (w-150, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    
                    cv2.imshow(f"Viam Camera: {CAMERA_NAME} (Multi-file)", overlay_frame)
                    
                    # Check for 'q' key press to quit
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print(f"\n🛑 Live feed window closed by user")
                        stop.set()
                
                # Progress indicator every 200 frames
                if frame_count % 200 == 0:
                    duration = frame_count / FPS
                    print(f"📊 Recording progress: {frame_count} frames ({duration:.1f} seconds) | Videos created: {len(video_files_created)}")
                    
            except Exception as e:
                print(f"⚠️  Warning: Frame capture error: {e}")
                await asyncio.sleep(0.1)  # Brief pause before retrying
                
            await asyncio.sleep(1 / FPS)
    finally:
        # Close any active writer
        if current_writer is not None:
            current_writer.release()
            if current_video_file:
                duration = sequence_frame_count / FPS
                print(f"✅ Final video completed: {current_video_file} ({sequence_frame_count} frames, {duration:.1f}s)")
                logger.end_sequence(f"Final video saved: {current_video_file}")
        
        await robot.close()
        coach.recording_active = False
        
        if SHOW_LIVE_FEED:
            cv2.destroyAllWindows()
            
        duration = frame_count / FPS
        
        # Log session end
        logger.log_phase_change("Recording session ended", f"Total duration: {duration:.1f}s, Total frames: {frame_count}, Videos created: {len(video_files_created)}")
        
        print(f"\n✅ Multi-file recording completed!")
        print(f"   Total frames processed: {frame_count}")
        print(f"   Total session duration: {duration:.1f} seconds")
        print(f"   Video files created: {len(video_files_created)}")
        
        for i, video_file in enumerate(video_files_created, 1):
            print(f"     {i}. {video_file}")
            
        print(f"   Detailed action log saved to: {LOG_FILE}")
        print(f"   Ground truth file saved to: {GT_FILE}")

async def main():
    """Main function that runs coaching and recording concurrently."""
    print("\n🎬 INTERACTIVE RECORDING SESSION")
    print("=" * 50)
    print(f"📁 Output directory: {args.output_dir}")
    print(f"📊 Ground truth file: {GT_FILE}")
    print(f"📋 Detailed log file: {LOG_FILE}")
    print("=" * 50)
    
    # Initialize logger
    logger = ActionLogger(LOG_FILE, GT_FILE)
    coach = CookingCoach(logger)
    
    # Do setup phase with clear prompts
    print("\n🔧 Starting setup phase...")
    try:
        await coach.setup_phase()
        print("✅ Setup phase completed!")
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return
    
    print("\n🚀 Setup complete! Starting recording and coaching...")
    print("📝 Note: You'll see prompts in this terminal while the video records")
    
    # Start both recording and coaching concurrently
    recording_task = asyncio.create_task(record_video(coach, logger))
    
    # Give recording a moment to start
    await asyncio.sleep(2)
    
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
        
        print(f"\n✅ Session complete! Check your files:")
        print(f"   📹 Videos: {args.output_dir}/{OUT_FILE_PREFIX}_*.mp4")
        print(f"   📊 Detailed log: {LOG_FILE}")
        print(f"   📊 Ground truth: {GT_FILE}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 Session ended. Check your files:")
        print(f"   Videos: {args.output_dir}/{OUT_FILE_PREFIX}_*.mp4")
        print(f"   Detailed log: {LOG_FILE}")
        print(f"   Ground truth: {GT_FILE}")
        sys.exit(0) 