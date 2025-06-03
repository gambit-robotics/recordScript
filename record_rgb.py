#!/usr/bin/env python3
"""
Grab frames from a Viam camera in real time and save them to MP4.
Stop with Ctrl‑C.
"""

import asyncio, os, signal, cv2, numpy as np
from viam.robot.client import RobotClient
from viam.rpc.dial import DialOptions
from viam.components.camera import Camera
from viam.media.video import CameraMimeType

# ---------------------------------------------------------------------
# Config – change only these four lines
CAMERA_NAME = "overhead-rgb"   # the name in your Viam config
FPS         = 10               # playback + capture rate
OUT_FILE    = "overhead_rgb_live.mp4"
# ---------------------------------------------------------------------

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

async def record():
    robot = await connect()
    cam   = Camera.from_robot(robot, CAMERA_NAME)

    # Get first frame to discover resolution
    viam_img   = await cam.get_image(CameraMimeType.JPEG)
    frame      = cv2.imdecode(np.frombuffer(viam_img, np.uint8),
                              cv2.IMREAD_COLOR)
    h, w       = frame.shape[:2]
    fourcc     = cv2.VideoWriter_fourcc(*"mp4v")
    writer     = cv2.VideoWriter(OUT_FILE, fourcc, FPS, (w, h))

    print(f"Recording {CAMERA_NAME} → {OUT_FILE}  (Ctrl‑C to stop)")

    # Graceful Ctrl‑C so the file header finalises
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    try:
        while not stop.is_set():
            viam_img = await cam.get_image(CameraMimeType.JPEG)
            frame    = cv2.imdecode(np.frombuffer(viam_img, np.uint8),
                                    cv2.IMREAD_COLOR)
            writer.write(frame)
            await asyncio.sleep(1 / FPS)
    finally:
        writer.release()
        await robot.close()
        print("✓ Saved", OUT_FILE)

if __name__ == "__main__":
    asyncio.run(record()) 