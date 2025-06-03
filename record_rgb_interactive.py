#!/usr/bin/env python3
"""
Interactive Viam camera recording with cooking action coaching.
Guides users through a series of cooking actions while recording video.
Stop with Ctrl‑C.
"""

import asyncio, os, signal, cv2, numpy as np, sys
from viam.robot.client import RobotClient
from viam.rpc.dial import DialOptions
from viam.components.camera import Camera
from viam.media.video import CameraMimeType

# ---------------------------------------------------------------------
# Config – change only these four lines
CAMERA_NAME = "overhead-rgb"   # the name in your Viam config
FPS         = 10               # playback + capture rate
OUT_FILE    = "cooking_actions_recording.mp4"
# ---------------------------------------------------------------------

class CookingCoach:
    def __init__(self):
        self.current_step = 0
        self.total_steps = 0
        self.setup_complete = False
        self.recording_active = False
        
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
            await self.get_user_input(
                f"Step {i+1}/{count}: {action_name}\n"
                f"Get ready to perform this action..."
            )
            
            if i < count - 1:  # Don't wait after the last action
                print(f"⏳ Waiting {delay} seconds before next action...")
                await asyncio.sleep(delay)
                
    async def run_coaching_sequence(self):
        """Run the complete coaching sequence."""
        if not self.setup_complete:
            await self.setup_phase()
            
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
            
        print(f"\n🎉 EXCELLENT! All cooking actions completed!")
        print("Recording will continue until you press Ctrl-C")
        print("Feel free to practice more or try variations!")

async def connect() -> RobotClient:
    """Connect to the robot via the Viam Cloud."""
    opts = RobotClient.Options(
        dial_options=DialOptions.with_api_key(
            api_key_id=os.environ["VIAM_API_KEY_ID"],
            api_key=os.environ["VIAM_API_KEY"]
        ),
        disable_webrtc=True        # headless client – no SDP exchange
    )
    return await RobotClient.at_address(os.environ["VIAM_ADDRESS"], opts)

async def record_video(coach):
    """Handle video recording while coaching runs."""
    robot = await connect()
    cam = Camera.from_robot(robot, CAMERA_NAME)

    # Get first frame to discover resolution
    viam_img = await cam.get_image(CameraMimeType.JPEG)
    frame = cv2.imdecode(np.frombuffer(viam_img, np.uint8), cv2.IMREAD_COLOR)
    h, w = frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUT_FILE, fourcc, FPS, (w, h))

    print(f"🎥 Recording {CAMERA_NAME} → {OUT_FILE}")
    coach.recording_active = True

    # Graceful Ctrl‑C handling
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    try:
        while not stop.is_set():
            viam_img = await cam.get_image(CameraMimeType.JPEG)
            frame = cv2.imdecode(np.frombuffer(viam_img, np.uint8), cv2.IMREAD_COLOR)
            writer.write(frame)
            await asyncio.sleep(1 / FPS)
    finally:
        writer.release()
        await robot.close()
        coach.recording_active = False
        print(f"\n✅ Video saved: {OUT_FILE}")

async def main():
    """Main function that runs coaching and recording concurrently."""
    coach = CookingCoach()
    
    # Run setup first, then start recording and coaching in parallel
    await coach.setup_phase()
    
    # Start both recording and coaching concurrently
    recording_task = asyncio.create_task(record_video(coach))
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
        print(f"\n👋 Session ended. Check your video file: {OUT_FILE}")
        sys.exit(0) 