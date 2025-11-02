# IoT Garage Management System

A comprehensive Flask-based IoT garage management system with real-time occupancy tracking, car event logging, and a beautiful dashboard interface.

## Features

### 🚗 Core Functionality
- **Real-time occupancy tracking** - Monitor parking slot status in real-time
- **Car event logging** - Track vehicle entry/exit with license plate recognition
- **Historical data** - Maintain complete history of occupancy changes
- **Visual garage map** - Interactive 2D layout of parking slots
- **Comprehensive dashboard** - Beautiful web interface with live updates

### 📊 API Endpoints

| Method | Endpoint | Description | Example Response |
|--------|----------|-------------|------------------|
| `POST` | `/api/update` | ESP32 posts occupancy update | `{"slot_id": "A1", "occupied": true}` |
| `POST` | `/api/car_event` | Log car entry/exit with license | `{"plate": "ABC123", "event": "enter"}` |
| `GET` | `/api/occupancy` | List all slots & status | `[{"slot_id":"A1","occupied":true}, ...]` |
| `GET` | `/api/summary` | Aggregated stats | `{"total": 10, "occupied": 6, "available": 4}` |
| `GET` | `/api/map` | Garage layout with occupancy | `{"rows": 2, "cols": 5, "slots": [...]}` |
| `GET` | `/api/history` | Past occupancy timeline | `[{"slot":"A1","occupied":true,"time":"..."}, ...]` |
| `GET` | `/api/car_log` | Car entry/exit history | `[{"plate":"ABC123","event":"enter","time":"..."}, ...]` |
| `GET` | `/` | Dashboard interface | HTML page |

### 🗂️ Database Schema

**Slots Table**
- `id` (Primary Key)
- `slot_id` (Unique identifier like "A1", "B2")
- `occupied` (Boolean status)
- `x`, `y` (Grid coordinates)
- `updated_at` (Last update timestamp)

**Occupancy History**
- `id` (Primary Key)
- `slot_id` (Reference to slot)
- `occupied` (Status change)
- `timestamp` (When change occurred)

**Car Events**
- `id` (Primary Key)
- `plate` (License plate)
- `event` ('enter' or 'exit')
- `timestamp` (Event time)

## Installation & Setup

### 1. Clone and Setup
```bash
cd c:\Users\nguye\Desktop\garage-iot
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

The server will start on `http://localhost:5000`

### 3. Access the Dashboard
Open your browser and navigate to `http://localhost:5000` to see the dashboard.

## Project Structure

```
garage-iot/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy ORM models
├── requirements.txt    # Python dependencies
├── templates/
│   └── dashboard.html  # Dashboard template
├── static/
│   └── js/
│       └── dashboard.js # Dashboard JavaScript
└── data/
    └── garage.db       # SQLite database (auto-created)
```

## Usage Examples

### License Detection
```bash
python license-detector/main.py
```

### ESP32 Integration

**Update Slot Occupancy:**
```bash
curl -X POST http://localhost:5000/api/update \
  -H "Content-Type: application/json" \
  -d '{"slot_id": "A1", "occupied": true}'
```

**Log Car Event:**
```bash
curl -X POST http://localhost:5000/api/car_event \
  -H "Content-Type: application/json" \
  -d '{"plate": "ABC123", "event": "enter"}'
```

### Query Data

**Get Garage Summary:**
```bash
curl http://localhost:5000/api/summary
```

**Get Occupancy Map:**
```bash
curl http://localhost:5000/api/map
```

**Get Car Log:**
```bash
curl http://localhost:5000/api/car_log?limit=10
```

## Dashboard Features

### 📊 Statistics Cards
- Total parking slots
- Currently occupied slots
- Available slots
- Occupancy rate percentage

### 🗺️ Interactive Garage Map
- Visual 2D grid layout
- Color-coded slot status (green=available, red=occupied)
- Click slots for detailed information
- Auto-refresh every 30 seconds

### 🚗 Real-time Event Logs
- Recent car entry/exit events
- Occupancy change history
- Timestamp formatting (relative time)

### 🔄 Auto-refresh
- Dashboard updates every 30 seconds
- Manual refresh button available
- Error handling and notifications

## Configuration

The system comes pre-configured with a 2x5 grid (10 parking slots: A1-A5, B1-B5). You can modify the default slots in `app.py`:

```python
default_slots = [
    {'slot_id': 'A1', 'x': 0, 'y': 0},
    {'slot_id': 'A2', 'x': 1, 'y': 0},
    # ... add more slots as needed
]
```

## ESP32 Integration Guide

To integrate with ESP32 devices:

1. **Occupancy Sensors**: Use ultrasonic or magnetic sensors to detect car presence
2. **Camera Module**: Implement license plate recognition
3. **WiFi Connection**: Connect ESP32 to your network
4. **HTTP Requests**: Use ESP32 HTTP client to send data to the Flask API

Example ESP32 code structure:
```cpp
// POST to /api/update when occupancy changes
// POST to /api/car_event when license plate detected
```

## Production Deployment

For production use:
1. Replace SQLite with PostgreSQL/MySQL
2. Use a proper WSGI server (Gunicorn)
3. Add authentication and security
4. Implement rate limiting
5. Add monitoring and logging

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.