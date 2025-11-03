"""
Test script for the complete license plate detection flow
"""

import requests
import json

ESP32_IP = "http://localhost:81"

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
try:
    response = requests.get(ESP32_IP + "/capture")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Image size: {len(response.content)} bytes")
    print("✓ Successfully fetched image\n")
except Exception as e:
    print(f"✗ Failed to capture image: {e}\n")

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

# Test 5: Slot 2 reports occupied (car just entered)
print("\n" + "=" * 70)
print("Test 5: Slot 2 Occupied After Entry")
print("=" * 70)
try:
    response = requests.post(
        "http://localhost:5000/api/update",
        json={"slot_id": "2", "occupied": True},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("✓ Slot 2 marked as occupied\n")
except Exception as e:
    print(f"✗ Failed to update slot 2: {e}\n")

# Test 6: Slot 2 available and car exit event
print("\n" + "=" * 70)
print("Test 6: Slot 2 Available, Car Exit Event")
print("=" * 70)
try:
    # Slot 2 available
    response = requests.post(
        "http://localhost:5000/api/update",
        json={"slot_id": "2", "occupied": False},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("✓ Slot 2 marked as available\n")

    # Log car exit event (simulate same plate as last entry if available)
    last_plate = None
    try:
        logs = requests.get("http://localhost:5000/api/car_log").json()
        for log in logs:
            if log['event'] == 'enter':
                last_plate = log['plate']
                break
    except Exception:
        pass
    if last_plate:
        response = requests.post(
            "http://localhost:5000/api/car_event",
            json={"plate": last_plate, "event": "exit"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Exit event status: {response.status_code}")
        print(f"Exit event response: {response.json()}")
        print("✓ Car exit event logged\n")
    else:
        print("✗ Could not find last entered plate to log exit event\n")
except Exception as e:
    print(f"✗ Failed to update slot 2 or log exit: {e}\n")
