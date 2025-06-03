#!/usr/bin/env python3
"""
Test connection to Viam robot and camera.
Quick verification script to check your setup without recording.
"""

import asyncio, os
from dotenv import load_dotenv
from viam.robot.client import RobotClient
from viam.rpc.dial import DialOptions
from viam.components.camera import Camera
from viam.media.video import CameraMimeType

# Load environment variables from .env file
load_dotenv()

# Camera name to test
CAMERA_NAME = os.environ.get("VIAM_CAMERA_NAME", "overhead-rgb")  # Camera name from Viam config

async def test_connection():
    """Test connection to robot and camera."""
    
    # Check environment variables
    print("🔍 Checking environment variables...")
    required_vars = ["VIAM_API_KEY_ID", "VIAM_API_KEY", "VIAM_ADDRESS"]
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: NOT SET")
        else:
            # Show partial values for security
            if var == "VIAM_API_KEY_ID":
                print(f"✅ {var}: {value[:20]}...")
            elif var == "VIAM_API_KEY":
                print(f"✅ {var}: {value[:10]}...")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nSet them with:")
        print("Option 1 - Shell environment:")
        for var in missing_vars:
            print(f'export {var}="your_value_here"')
        print("\nOption 2 - .env file:")
        print("Create a .env file with:")
        for var in missing_vars:
            print(f'{var}="your_value_here"')
        return False
    
    print("\n🔌 Testing robot connection...")
    
    try:
        # Connect to robot
        opts = RobotClient.Options(
            dial_options=DialOptions.with_api_key(
                api_key_id=os.environ["VIAM_API_KEY_ID"],
                api_key=os.environ["VIAM_API_KEY"]
            )
        )
        
        robot = await RobotClient.at_address(os.environ["VIAM_ADDRESS"], opts)
        print("✅ Successfully connected to Viam robot!")
        
        # Get robot status and resources
        try:
            # List available resources
            resource_names = await robot.resource_names()
            print(f"📋 Robot resources: {len(resource_names)} found")
            
            cameras = [name for name in resource_names if name.namespace == "rdk" and name.type == "camera"]
            
            if cameras:
                print(f"📷 Available cameras:")
                for cam in cameras:
                    print(f"   • {cam.name}")
            else:
                print("⚠️  No cameras found in robot configuration")
                
        except Exception as e:
            print(f"⚠️  Could not get robot details: {e}")
        
        # Test camera connection
        print(f"\n📷 Testing camera connection: '{CAMERA_NAME}'")
        try:
            cam = Camera.from_robot(robot, CAMERA_NAME)
            print("✅ Successfully connected to camera!")
            
            # Test getting a frame
            print("🖼️  Testing frame capture...")
            viam_img = await cam.get_image(CameraMimeType.JPEG)
            
            # Convert ViamImage to bytes
            img_bytes = viam_img.data
            print(f"✅ Successfully captured frame ({len(img_bytes)} bytes)")
            
            # Decode frame to get resolution
            import cv2, numpy as np
            frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            h, w = frame.shape[:2]
            print(f"📐 Frame resolution: {w}x{h}")
            
        except Exception as e:
            print(f"❌ Camera connection failed: {e}")
            print(f"Make sure '{CAMERA_NAME}' matches your robot configuration")
            await robot.close()
            return False
        
        await robot.close()
        
        print(f"\n🎉 SUCCESS! Your Viam setup is working correctly!")
        print(f"You're ready to start recording with:")
        print(f"   python3 record.py")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("• Check your robot is online at app.viam.com")
        print("• Verify your API key is active and has the right permissions")
        print("• Make sure your machine address is correct")
        return False

async def main():
    print("🧪 Viam Connection Test")
    print("=" * 40)
    
    success = await test_connection()
    
    if not success:
        print(f"\n💡 Need help? Check the README.md for troubleshooting tips!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 