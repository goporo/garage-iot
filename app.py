from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime, timedelta, timezone
import os
import sys
from dotenv import load_dotenv
import threading

# Load environment variables
TOTAL_SLOT = 4  # Total parking slots in the garage

load_dotenv()

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "data", "garage.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models and initialize database
from models import db, Slot, OccupancyHistory, CarEvent



# Import license plate detector using sys.path and cwd trick for hyphenated folder
license_detector_path = os.path.join(basedir, 'license-detector')
sys.path.append(license_detector_path)
original_cwd = os.getcwd()
os.chdir(license_detector_path)
from main import LicensePlateDetector
detector = LicensePlateDetector()
os.chdir(original_cwd)

db.init_app(app)

# Create tables
with app.app_context():
    os.makedirs(os.path.join(basedir, 'data'), exist_ok=True)
    db.create_all()
    
    # Initialize with default slots if empty
    if Slot.query.count() == 0:
        default_slots = [
            {'slot_id': '1'},
            {'slot_id': '2'},
            {'slot_id': '3'},
            {'slot_id': '4'},
        ]
        for slot_data in default_slots:
            slot = Slot(
                slot_id=slot_data['slot_id'],
                occupied=False
            )
            db.session.add(slot)
        db.session.commit()

# Track pending reservations (count only, not specific slots)
pending_reservations = 0

# API Routes
@app.route('/api/update', methods=['POST'])
def update_occupancy():
    """ESP32 posts occupancy update"""
    try:
        data = request.get_json()
        slot_id = data.get('slot_id')
        occupied = data.get('occupied')
        
        if not slot_id or occupied is None:
            return jsonify({'error': 'Missing slot_id or occupied status'}), 400
        
        # Find and update slot
        slot = Slot.query.filter_by(slot_id=slot_id).first()
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        # Only update if status changed
        if slot.occupied != occupied:
            slot.occupied = occupied
            slot.updated_at = datetime.utcnow() + timedelta(hours=7)
            # Log history
            history = OccupancyHistory(
                slot_id=slot_id,
                occupied=occupied,
                timestamp=datetime.utcnow() + timedelta(hours=7)
            )
            db.session.add(history)
            db.session.commit()
        return jsonify({'success': True, 'slot_id': slot_id, 'occupied': occupied})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/car_event', methods=['POST'])
def add_car_event():
    """ESP32 (camera or sensor) logs entry/exit with license"""
    global pending_reservations
    try:
        data = request.get_json()
        plate = data.get('plate')
        event = data.get('event')
        
        if not plate or not event:
            return jsonify({'error': 'Missing plate or event'}), 400
        
        if event not in ['enter', 'exit']:
            return jsonify({'error': 'Event must be "enter" or "exit"'}), 400
        
        new_event = CarEvent(
            plate=plate,
            event=event,
            timestamp=datetime.utcnow() + timedelta(hours=7)
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        # Decrement pending reservations when car exits (increase available slots)
        if event == 'exit':
            pending_reservations = max(pending_reservations - 1, 0)
        
        return jsonify({'success': True, 'plate': plate, 'event': event})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect_plate', methods=['POST'])
def detect_plate():
    """Trigger async license plate detection from ESP32 camera"""
    global pending_reservations
    try:
        if detector is None:
            return jsonify({'error': 'License plate detector not initialized'}), 500

        data = request.get_json(silent=True) or {}
        event_type = data.get('event', 'enter')
        if event_type not in ['enter', 'exit']:
            return jsonify({'error': 'Event must be "enter" or "exit"'}), 400

        esp32_url = os.getenv('ESP32_CAMERA_URL', 'http://192.168.1.19/capture')

        # Increment pending reservations immediately (reduce available count)
        if event_type == 'enter':
            pending_reservations = min(TOTAL_SLOT, pending_reservations + 1)
        
        # Do the heavy work in a background thread
        threading.Thread(
            target=process_plate_detection,
            args=(esp32_url, event_type),
            daemon=True
        ).start()

        # Respond immediately
        return jsonify({'status': 'processing', 'event': event_type}), 202
    except Exception as e:
        print(f"Error in detect_plate trigger: {e}")
        return jsonify({'error': str(e)}), 500

def process_plate_detection(esp32_url, event_type):
    """Background worker for actual image detection."""
    with app.app_context():  # <-- add this
        try:
            print(f"[Worker] Fetching image from ESP32: {esp32_url}")
            image = detector.fetch_esp32_image(esp32_url)
            if image is None:
                print("[Worker] Failed to fetch image")
                return

            print("[Worker] Processing image...")
            now_gmt7 = datetime.utcnow() + timedelta(hours=7)
            image_filename = f'esp32_capture_{now_gmt7.strftime("%Y%m%d_%H%M%S")}.jpg'
            image_path = os.path.join(basedir, 'data', image_filename)

            results = detector.process_image(image, save_result=True, output_path=image_path)
            if not results:
                print("[Worker] No license plate detected")
                return

            first_plate = results[0]['plate_number']
            confidence = results[0]['confidence']
            rel_image_uri = f'/data/{image_filename}'

            new_event = CarEvent(
                plate=first_plate,
                event=event_type,
                timestamp=datetime.utcnow() + timedelta(hours=7),
                image_path=rel_image_uri
            )
            db.session.add(new_event)
            db.session.commit()
            print(f"[Worker] Saved event for plate {first_plate} ({confidence:.2f})")

        except Exception as e:
            db.session.rollback()
            print(f"[Worker Error] {e}")

# Serve images from /data directory
@app.route('/data/<path:filename>')
def serve_data_file(filename):
    return send_from_directory(os.path.join(basedir, 'data'), filename)

@app.route('/api/occupancy', methods=['GET'])
def get_occupancy():
    """List all slots & status"""
    try:
        slots = Slot.query.all()
        return jsonify([slot.as_dict() for slot in slots])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Aggregated stats (total, occupied, available)"""
    try:
        # Use only in-memory counters for summary
        global pending_reservations
        # Initial slot count is fixed at startup
        total = TOTAL_SLOT
        occupied = pending_reservations
        available = total - occupied
        return jsonify({
            'total': total,
            'occupied': occupied,
            'available': available,
            'occupancy_rate': round((occupied / total * 100) if total > 0 else 0, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map', methods=['GET'])
def get_map():
    """Layout map of garage with occupancy"""
    try:
        slots = Slot.query.all()
        # Return actual slot status (don't mark any as occupied for pending reservations)
        return jsonify([slot.as_dict() for slot in slots])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Past occupancy timeline"""
    try:
        limit = request.args.get('limit', 50, type=int)
        slot_id = request.args.get('slot_id')
        
        query = OccupancyHistory.query
        
        if slot_id:
            query = query.filter_by(slot_id=slot_id)
        
        history = query.order_by(OccupancyHistory.timestamp.desc()).limit(limit).all()
        
        return jsonify([h.as_dict() for h in history])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/car_log', methods=['GET'])
def get_car_log():
    """History of car entry/exit events"""
    try:
        limit = request.args.get('limit', 20, type=int)
        logs = CarEvent.query.order_by(CarEvent.timestamp.desc()).limit(limit).all()
        
        return jsonify([log.as_dict() for log in logs])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard route
@app.route('/')
def dashboard():
    """Renders dashboard (HTML+JS)"""
    refresh_interval = int(os.getenv('DASHBOARD_REFRESH_INTERVAL', 3000))
    return render_template('dashboard.html', refresh_interval=refresh_interval)

# Health check
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': (datetime.utcnow() + timedelta(hours=7)).isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)