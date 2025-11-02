"""
Mock ESP32 Camera Server
Simulates ESP32 with OV2640 camera for testing license plate detection
"""

from flask import Flask, send_file, jsonify
from pathlib import Path
import random

app = Flask(__name__)

# Path to test images
TEST_IMAGES_DIR = Path(__file__).parent / 'license-detector' / 'test'

@app.route('/capture')
def capture():
    """Simulate ESP32 camera capture endpoint"""
    try:
        # Get all test images (exclude result images)
        image_files = [f for f in TEST_IMAGES_DIR.glob("*.jpg") 
                      if not f.name.startswith('result_')]
        image_files += [f for f in TEST_IMAGES_DIR.glob("*.png") 
                       if not f.name.startswith('result_')]
        
        if not image_files:
            return jsonify({'error': 'No test images available'}), 404
        
        # Return a random test image
        selected_image = random.choice(image_files)
        print(f"Serving mock capture: {selected_image.name}")
        
        return send_file(str(selected_image), mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """Mock ESP32 status endpoint"""
    return jsonify({
        'camera': 'OV2640',
        'status': 'ready',
        'resolution': '1280x720',
        'mock': True
    })

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'device': 'Mock ESP32 Camera',
        'camera': 'OV2640',
        'endpoints': {
            '/capture': 'Get camera image',
            '/status': 'Get camera status'
        }
    })

if __name__ == '__main__':
    print("=" * 70)
    print("Mock ESP32 Camera Server (OV2640)")
    print("=" * 70)
    print("Simulating ESP32 camera at http://localhost:81")
    print(f"Test images from: {TEST_IMAGES_DIR}")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=81)
