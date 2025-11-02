"""
Test script for the complete license plate detection flow
"""

import requests
import json

ESP32_IP = "http://192.168.1.10"

# Test 1: Check mock ESP32
print("=" * 70)
print("Test 1: Check Mock ESP32 Camera")
print("=" * 70)
try:
    response = requests.get(ESP32_IP + "/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("✓ Mock ESP32 is running\n")
except Exception as e:
    print(f"✗ Mock ESP32 not accessible: {e}\n")

# Test 2: Get image from mock ESP32
print("=" * 70)
print("Test 2: Capture Image from Mock ESP32")
print("=" * 70)

MAX_RETRIES = 3
TIMEOUT = 10  # seconds

for attempt in range(MAX_RETRIES):
    try:
        print(f"\nAttempt {attempt + 1}/{MAX_RETRIES}:")
        response = requests.get(ESP32_IP + "/capture", timeout=TIMEOUT, stream=True)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        # Get content length if available
        content_length = response.headers.get('Content-Length')
        if content_length:
            print(f"Expected image size: {content_length} bytes")
        
        # Download with progress
        content = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                content.extend(chunk)
                print(f"Downloaded: {len(content)} bytes", end='\r')
        
        print(f"\nActual image size: {len(content)} bytes")
        
        # Save the captured image for debug
        import os
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_image_path = os.path.join("uploads", f"captured_{timestamp}.jpg")
        with open(debug_image_path, "wb") as f:
            f.write(content)
        print(f"Debug image saved to: {debug_image_path}\n")
        
        print("✓ Successfully fetched image\n")
        break  # Success, exit retry loop
        
    except requests.exceptions.Timeout:
        print(f"✗ Request timed out after {TIMEOUT} seconds")
        if attempt < MAX_RETRIES - 1:
            print("Retrying...")
        else:
            print("Max retries reached")
            raise
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to capture image: {e}")
        if attempt < MAX_RETRIES - 1:
            print("Retrying...")
        else:
            print("Max retries reached")
            raise

# Test 3: Call detect_plate endpoint
print("=" * 70)
print("Test 3: Detect License Plate")
print("=" * 70)
try:
    response = requests.post(
        "http://localhost:5000/api/detect_plate",
        json={"event": "enter", "esp32_url": ESP32_IP},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print(f"\n✓ Successfully detected plate: {result.get('plate')}")
        print(f"  Event: {result.get('event')}")
        print(f"  Total detected: {result.get('total_detected')}")
    else:
        print(f"\n✗ Detection failed: {result.get('error')}")
except Exception as e:
    print(f"✗ Failed to call detect_plate: {e}\n")

# Test 4: Check car log
print("\n" + "=" * 70)
print("Test 4: Check Car Event Log")
print("=" * 70)
try:
    response = requests.get("http://localhost:5000/api/car_log")
    print(f"Status: {response.status_code}")
    logs = response.json()
    print(f"Total events: {len(logs)}")
    
    if logs:
        print("\nRecent events:")
        for log in logs[:5]:
            print(f"  - {log['plate']}: {log['event']} at {log['timestamp']}")
    print("\n✓ Successfully retrieved car log")
except Exception as e:
    print(f"✗ Failed to get car log: {e}\n")
