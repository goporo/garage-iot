from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Slot(db.Model):
    """Current slot state"""
    __tablename__ = 'slots'
    
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.String(10), unique=True, nullable=False)
    occupied = db.Column(db.Boolean, default=False, nullable=False)
    # Removed x and y fields for simplicity
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def as_dict(self):
        return {
            'id': self.id,
            'slot_id': self.slot_id,
            'occupied': self.occupied,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Slot {self.slot_id}: {"Occupied" if self.occupied else "Available"}>'

class OccupancyHistory(db.Model):
    """Changes over time"""
    __tablename__ = 'occupancy_history'
    
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.String(10), nullable=False)
    occupied = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def as_dict(self):
        return {
            'id': self.id,
            'slot_id': self.slot_id,
            'occupied': self.occupied,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self):
        return f'<History {self.slot_id}: {"Occupied" if self.occupied else "Available"} at {self.timestamp}>'

class CarEvent(db.Model):
    """Vehicle log"""
    __tablename__ = 'car_events'
    
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(20), nullable=False)
    event = db.Column(db.String(10), nullable=False)  # 'enter' or 'exit'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    image_path = db.Column(db.String(256), nullable=True)  # Path to captured image
    
    def as_dict(self):
        return {
            'id': self.id,
            'plate': self.plate,
            'event': self.event,
            'timestamp': self.timestamp.isoformat(),
            'image_path': self.image_path
        }
    
    def __repr__(self):
        return f'<CarEvent {self.plate}: {self.event} at {self.timestamp}>'