from flask import Flask, request, jsonify, render_template
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "data", "garage.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models and initialize database
from models import db, Slot, OccupancyHistory, CarEvent
db.init_app(app)

# Create tables
with app.app_context():
    os.makedirs(os.path.join(basedir, 'data'), exist_ok=True)
    db.create_all()
    
    # Initialize with default slots if empty
    if Slot.query.count() == 0:
        default_slots = [
            {'slot_id': 'A1', 'x': 0, 'y': 0},
            {'slot_id': 'A2', 'x': 1, 'y': 0},
            {'slot_id': 'A3', 'x': 2, 'y': 0},
            {'slot_id': 'A4', 'x': 3, 'y': 0},
            {'slot_id': 'A5', 'x': 4, 'y': 0},
            {'slot_id': 'B1', 'x': 0, 'y': 1},
            {'slot_id': 'B2', 'x': 1, 'y': 1},
            {'slot_id': 'B3', 'x': 2, 'y': 1},
            {'slot_id': 'B4', 'x': 3, 'y': 1},
            {'slot_id': 'B5', 'x': 4, 'y': 1},
        ]
        
        for slot_data in default_slots:
            slot = Slot(
                slot_id=slot_data['slot_id'],
                x=slot_data['x'],
                y=slot_data['y'],
                occupied=False
            )
            db.session.add(slot)
        db.session.commit()

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
            slot.updated_at = datetime.utcnow()
            
            # Log history
            history = OccupancyHistory(
                slot_id=slot_id,
                occupied=occupied,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(history)
            db.session.commit()
        
        return jsonify({'success': True, 'slot_id': slot_id, 'occupied': occupied})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/car_event', methods=['POST'])
def add_car_event():
    """ESP32 (camera or sensor) logs entry/exit with license"""
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
            timestamp=datetime.utcnow()
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({'success': True, 'plate': plate, 'event': event})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        total = Slot.query.count()
        occupied = Slot.query.filter_by(occupied=True).count()
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
        
        # Calculate grid dimensions
        max_x = max(slot.x for slot in slots) if slots else 0
        max_y = max(slot.y for slot in slots) if slots else 0
        
        layout = {
            'rows': max_y + 1,
            'cols': max_x + 1,
            'slots': [slot.as_dict() for slot in slots]
        }
        
        return jsonify(layout)
    
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
    return render_template('dashboard.html')

# Health check
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)