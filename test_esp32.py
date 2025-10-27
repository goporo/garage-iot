# ESP32 Test Scripts for IoT Garage System

import requests
import json
import time
import random

# Configuration
BASE_URL = "http://localhost:5000"
SLOT_IDS = ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4", "B5"]
SAMPLE_PLATES = ["ABC123", "XYZ789", "DEF456", "GHI321", "JKL654", "MNO987"]

def update_slot_occupancy(slot_id, occupied):
    """Simulate ESP32 updating slot occupancy"""
    url = f"{BASE_URL}/api/update"
    data = {
        "slot_id": slot_id,
        "occupied": occupied
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ Updated {slot_id}: {'Occupied' if occupied else 'Available'}")
        else:
            print(f"❌ Failed to update {slot_id}: {response.text}")
    except Exception as e:
        print(f"❌ Error updating {slot_id}: {e}")

def log_car_event(plate, event):
    """Simulate ESP32 logging car entry/exit"""
    url = f"{BASE_URL}/api/car_event"
    data = {
        "plate": plate,
        "event": event
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"🚗 Car event logged: {plate} - {event}")
        else:
            print(f"❌ Failed to log car event: {response.text}")
    except Exception as e:
        print(f"❌ Error logging car event: {e}")

def get_summary():
    """Get garage summary"""
    try:
        response = requests.get(f"{BASE_URL}/api/summary")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Summary: {data['occupied']}/{data['total']} occupied ({data['occupancy_rate']}%)")
        else:
            print(f"❌ Failed to get summary: {response.text}")
    except Exception as e:
        print(f"❌ Error getting summary: {e}")

def simulate_random_activity():
    """Simulate random garage activity"""
    print("🎯 Starting random garage simulation...")
    
    for i in range(20):
        # Random slot update
        slot_id = random.choice(SLOT_IDS)
        occupied = random.choice([True, False])
        update_slot_occupancy(slot_id, occupied)
        
        # Random car event (30% chance)
        if random.random() < 0.3:
            plate = random.choice(SAMPLE_PLATES)
            event = random.choice(["enter", "exit"])
            log_car_event(plate, event)
        
        # Show summary every 5 updates
        if (i + 1) % 5 == 0:
            get_summary()
            print("-" * 50)
        
        time.sleep(2)  # Wait 2 seconds between updates

def simulate_realistic_scenario():
    """Simulate a realistic parking scenario"""
    print("🏢 Simulating realistic parking scenario...")
    
    scenarios = [
        # Morning rush - cars entering
        ("ABC123", "enter", "A1", True),
        ("XYZ789", "enter", "A2", True),
        ("DEF456", "enter", "B1", True),
        ("GHI321", "enter", "B2", True),
        
        # Midday - some cars leaving
        ("ABC123", "exit", "A1", False),
        ("MNO987", "enter", "A3", True),
        
        # Afternoon - mixed activity
        ("DEF456", "exit", "B1", False),
        ("JKL654", "enter", "B3", True),
        ("XYZ789", "exit", "A2", False),
        
        # Evening - cars leaving
        ("GHI321", "exit", "B2", False),
        ("MNO987", "exit", "A3", False),
        ("JKL654", "exit", "B3", False),
    ]
    
    for plate, event, slot_id, occupied in scenarios:
        print(f"📍 Scenario: {plate} {event}s, updating {slot_id}")
        
        # Log car event first
        log_car_event(plate, event)
        time.sleep(1)
        
        # Update slot occupancy
        update_slot_occupancy(slot_id, occupied)
        time.sleep(2)
        
        # Show current status
        get_summary()
        print("-" * 50)
        time.sleep(3)

def test_all_endpoints():
    """Test all API endpoints"""
    print("🧪 Testing all API endpoints...")
    
    endpoints = [
        ("/api/summary", "GET"),
        ("/api/occupancy", "GET"),
        ("/api/map", "GET"),
        ("/api/history?limit=5", "GET"),
        ("/api/car_log?limit=5", "GET"),
        ("/health", "GET")
    ]
    
    for endpoint, method in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {method} {endpoint}: OK")
                
                # Show sample data for some endpoints
                if "summary" in endpoint:
                    print(f"   Summary: {data}")
                elif "map" in endpoint:
                    print(f"   Map: {data['rows']}x{data['cols']} grid, {len(data['slots'])} slots")
                elif "history" in endpoint:
                    print(f"   History: {len(data)} recent changes")
                elif "car_log" in endpoint:
                    print(f"   Car Log: {len(data)} recent events")
                    
            else:
                print(f"❌ {method} {endpoint}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ {method} {endpoint}: Error - {e}")
        
        time.sleep(1)

def clear_all_slots():
    """Clear all parking slots (set to available)"""
    print("🧹 Clearing all parking slots...")
    
    for slot_id in SLOT_IDS:
        update_slot_occupancy(slot_id, False)
        time.sleep(0.5)
    
    get_summary()

if __name__ == "__main__":
    print("🚀 IoT Garage Test Script")
    print("=" * 50)
    
    while True:
        print("\nSelect test scenario:")
        print("1. Test all endpoints")
        print("2. Clear all slots")
        print("3. Random activity simulation")
        print("4. Realistic scenario")
        print("5. Manual slot update")
        print("6. Manual car event")
        print("7. Show summary")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-7): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            test_all_endpoints()
        elif choice == "2":
            clear_all_slots()
        elif choice == "3":
            simulate_random_activity()
        elif choice == "4":
            simulate_realistic_scenario()
        elif choice == "5":
            slot_id = input("Enter slot ID (e.g., A1): ").strip().upper()
            occupied = input("Occupied? (y/n): ").strip().lower() == 'y'
            update_slot_occupancy(slot_id, occupied)
        elif choice == "6":
            plate = input("Enter license plate: ").strip().upper()
            event = input("Event (enter/exit): ").strip().lower()
            if event in ["enter", "exit"]:
                log_car_event(plate, event)
            else:
                print("❌ Invalid event. Use 'enter' or 'exit'")
        elif choice == "7":
            get_summary()
        else:
            print("❌ Invalid choice. Please try again.")