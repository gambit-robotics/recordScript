#!/usr/bin/env python3
"""
Grab frames from a Viam camera in real time and save them to MP4.
Stop with Ctrl‑C.
"""

import asyncio, os, signal, cv2, numpy as np
from dotenv import load_dotenv
from viam.robot.client import RobotClient
from viam.rpc.dial import DialOptions
from viam.components.camera import Camera
from viam.media.video import CameraMimeType

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------
# Config – change only these three lines
CAMERA_NAME = os.environ.get("VIAM_CAMERA_NAME", "overhead-rgb")  # Camera name from Viam config
FPS         = 10               # playback + capture rate
OUT_FILE    = "overhead_rgb_live.mp4"
SHOW_LIVE_FEED = True          # Display live camera feed window
# ---------------------------------------------------------------------

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

async def record():
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
    writer = cv2.VideoWriter(OUT_FILE, fourcc, FPS, (w, h))
    
    if not writer.isOpened():
        print(f"❌ Failed to create video writer for {OUT_FILE}")
        await robot.close()
        raise RuntimeError("Could not create video file")

    print(f"🎥 Recording started!")
    print(f"   Camera: {CAMERA_NAME}")
    print(f"   Output: {OUT_FILE}")
    print(f"   Resolution: {w}x{h}")
    print(f"   FPS: {FPS}")
    print(f"   Live feed: {'Enabled' if SHOW_LIVE_FEED else 'Disabled'}")
    print(f"📹 Recording... (Press Ctrl-C to stop)")
    
    if SHOW_LIVE_FEED:
        print(f"📺 Live feed window opened. Press 'q' in the video window or Ctrl-C to stop.")
        cv2.namedWindow(f"Viam Camera: {CAMERA_NAME}", cv2.WINDOW_AUTOSIZE)

    # Graceful Ctrl‑C so the file header finalises
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    frame_count = 0
    try:
        while not stop.is_set():
            try:
                viam_img = await cam.get_image(CameraMimeType.JPEG)
                frame = cv2.imdecode(np.frombuffer(viam_img.data, np.uint8), cv2.IMREAD_COLOR)
                writer.write(frame)
                frame_count += 1
                
                # Display live feed if enabled
                if SHOW_LIVE_FEED:
                    # Add recording indicator overlay
                    overlay_frame = frame.copy()
                    cv2.circle(overlay_frame, (30, 30), 15, (0, 0, 255), -1)  # Red circle
                    cv2.putText(overlay_frame, "REC", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Add frame counter
                    duration = frame_count / FPS
                    time_text = f"Frame: {frame_count} | Time: {duration:.1f}s"
                    cv2.putText(overlay_frame, time_text, (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    cv2.imshow(f"Viam Camera: {CAMERA_NAME}", overlay_frame)
                    
                    # Check for 'q' key press to quit
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print(f"\n🛑 Live feed window closed by user")
                        stop.set()
                
                # Progress indicator every 100 frames
                if frame_count % 100 == 0:
                    duration = frame_count / FPS
                    print(f"📊 Recorded {frame_count} frames ({duration:.1f} seconds)")
                    
            except Exception as e:
                print(f"⚠️  Warning: Frame capture error: {e}")
                await asyncio.sleep(0.1)  # Brief pause before retrying
                
            await asyncio.sleep(1 / FPS)
    finally:
        writer.release()
        await robot.close()
        
        if SHOW_LIVE_FEED:
            cv2.destroyAllWindows()
            
        duration = frame_count / FPS
        print(f"\n✅ Recording completed!")
        print(f"   Total frames: {frame_count}")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Saved to: {OUT_FILE}")

if __name__ == "__main__":
    asyncio.run(record()) 