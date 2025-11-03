# IoT Garage Management System

## Quickstart

```bash
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

## API

| Method | Endpoint           | Example Request/Response |
|--------|--------------------|--------------------------|
| POST   | /api/update        | `{ "slot_id": "1", "occupied": true }` |
| POST   | /api/car_event     | `{ "plate": "ABC123", "event": "enter" }` |
| POST   | /api/detect_plate
| GET    | /api/occupancy     | `[ { "slot_id": "1", "occupied": true }, ... ]` |
| GET    | /api/summary       | `{ "total": 4, "occupied": 1, "available": 3, "occupancy_rate": 25.0 }` |
| GET    | /api/map           | `[ { "slot_id": "1", "occupied": false, ... }, ... ]` |
| GET    | /api/history       | `[ { "slot_id": "1", "occupied": true, "timestamp": "..." }, ... ]` |
| GET    | /api/car_log       | `[ { "plate": "ABC123", "event": "enter", "timestamp": "..." }, ... ]` |
| GET    | /                  | Dashboard HTML           |