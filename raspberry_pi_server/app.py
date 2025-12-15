"""
Patient Security Management System (PSMS)
Raspberry Pi Backend Server

This Flask application receives sensor data from ESP8266 devices,
stores it locally and syncs to Google Cloud Platform.

Features:
- REST API endpoints for sensor data ingestion
- Local SQLite database storage
- Google Cloud Firestore integration
- Real-time alert notifications
- Data visualization endpoints
"""

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from datetime import datetime
import sqlite3
import json
import os
import random
import time
from typing import Dict, Any, Optional
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_PATH = 'psms_data.db'
CLOUD_SYNC_ENABLED = os.getenv('CLOUD_SYNC_ENABLED', 'false').lower() == 'true'
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

# Simulation settings (used until real ESP data is wired up)
SIMULATED_DEVICE_ID = os.getenv('SIMULATED_DEVICE_ID', 'ESP8266_PSMS_001')
SIMULATED_LOCATION = os.getenv('SIMULATED_LOCATION', 'Room_101')
SIMULATED_INTERVAL_SEC = float(os.getenv('SIMULATED_INTERVAL_SEC', '2.0'))

# Alert thresholds (can be overridden by environment variables)
ALERT_THRESHOLDS = {
    'air_quality': int(os.getenv('AIR_QUALITY_THRESHOLD', '600')),
    'temp_high': float(os.getenv('TEMP_HIGH_THRESHOLD', '30.0')),
    'temp_low': float(os.getenv('TEMP_LOW_THRESHOLD', '18.0')),
    'humidity_high': float(os.getenv('HUMIDITY_HIGH_THRESHOLD', '70.0')),
    'distance': int(os.getenv('DISTANCE_THRESHOLD', '50'))
}


def init_database():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create sensor_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            location TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            device_timestamp INTEGER,
            temperature REAL,
            humidity REAL,
            air_quality INTEGER,
            distance INTEGER,
            alert_type TEXT,
            alert_active BOOLEAN,
            synced_to_cloud BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            location TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            alert_message TEXT,
            severity TEXT DEFAULT 'medium',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0,
            resolved_at DATETIME
        )
    ''')
    
    # Create devices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            location TEXT,
            status TEXT DEFAULT 'active',
            last_seen DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_timestamp ON sensor_data(device_id, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_device ON alerts(device_id, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cloud_sync ON sensor_data(synced_to_cloud)')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def save_sensor_data(data: Dict[str, Any]) -> int:
    """
    Save sensor data to local database.
    
    Args:
        data: Dictionary containing sensor data
        
    Returns:
        ID of inserted record
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Extract data
        device_id = data.get('device_id', 'unknown')
        location = data.get('location', 'unknown')
        device_timestamp = data.get('timestamp', 0)
        sensors = data.get('sensors', {})
        alert_type = data.get('alert_type', 'none')
        alert_active = data.get('alert_active', False)
        
        # Insert sensor data
        cursor.execute('''
            INSERT INTO sensor_data 
            (device_id, location, device_timestamp, temperature, humidity, 
             air_quality, distance, alert_type, alert_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_id,
            location,
            device_timestamp,
            sensors.get('temperature'),
            sensors.get('humidity'),
            sensors.get('air_quality'),
            sensors.get('distance'),
            alert_type,
            alert_active
        ))
        
        record_id = cursor.lastrowid
        
        # Update device last_seen
        # Note: ON CONFLICT requires SQLite 3.24.0+ (available in Python 3.7+)
        cursor.execute('''
            INSERT INTO devices (device_id, location, last_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(device_id) DO UPDATE SET
                location = excluded.location,
                last_seen = CURRENT_TIMESTAMP
        ''', (device_id, location))
        
        # Create alert if needed
        if alert_active and alert_type != 'none':
            alert_message = generate_alert_message(alert_type, sensors)
            severity = get_alert_severity(alert_type)
            
            cursor.execute('''
                INSERT INTO alerts (device_id, location, alert_type, alert_message, severity)
                VALUES (?, ?, ?, ?, ?)
            ''', (device_id, location, alert_type, alert_message, severity))
            
            logger.warning(f"Alert created: {alert_type} for device {device_id}")
        
        conn.commit()
        logger.info(f"Sensor data saved: ID={record_id}, Device={device_id}")
        
        return record_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving sensor data: {e}")
        raise
    finally:
        conn.close()


def generate_alert_message(alert_type: str, sensors: Dict[str, Any]) -> str:
    """Generate human-readable alert message."""
    messages = {
        'poor_air_quality': f"Poor air quality detected: {sensors.get('air_quality', 'N/A')} ppm",
        'high_temperature': f"High temperature alert: {sensors.get('temperature', 'N/A')}°C",
        'low_temperature': f"Low temperature alert: {sensors.get('temperature', 'N/A')}°C",
        'high_humidity': f"High humidity alert: {sensors.get('humidity', 'N/A')}%",
        'door_intrusion': f"Unattended door activity detected: {sensors.get('distance', 'N/A')} cm"
    }
    return messages.get(alert_type, f"Alert: {alert_type}")


def get_alert_severity(alert_type: str) -> str:
    """Determine alert severity based on type."""
    high_severity = ['door_intrusion', 'poor_air_quality']
    if alert_type in high_severity:
        return 'high'
    return 'medium'


def simulate_sensor_payload() -> Dict[str, Any]:
    """Generate a simulated sensor payload for a single ESP device."""
    temperature = round(random.uniform(20.0, 28.0), 1)
    humidity = round(random.uniform(40.0, 65.0), 1)
    air_quality = random.randint(300, 650)
    distance = random.randint(20, 120)

    alert_type = 'none'
    alert_active = False

    if air_quality > ALERT_THRESHOLDS['air_quality']:
        alert_type = 'poor_air_quality'
        alert_active = True
    elif temperature > ALERT_THRESHOLDS['temp_high']:
        alert_type = 'high_temperature'
        alert_active = True
    elif temperature < ALERT_THRESHOLDS['temp_low']:
        alert_type = 'low_temperature'
        alert_active = True
    elif humidity > ALERT_THRESHOLDS['humidity_high']:
        alert_type = 'high_humidity'
        alert_active = True
    elif distance < ALERT_THRESHOLDS['distance']:
        alert_type = 'door_intrusion'
        alert_active = True

    payload: Dict[str, Any] = {
        'device_id': SIMULATED_DEVICE_ID,
        'location': SIMULATED_LOCATION,
        'timestamp': int(time.time()),
        'sensors': {
            'temperature': temperature,
            'humidity': humidity,
            'air_quality': air_quality,
            'distance': distance,
        },
        'alert_type': alert_type,
        'alert_active': alert_active,
    }

    return payload


def generate_device_stream():
    """Yield simulated device payloads at a fixed interval."""
    while True:
        payload = simulate_sensor_payload()
        try:
            save_sensor_data(payload)
        except Exception as exc:
            logger.error(f"Failed to persist simulated data: {exc}")
        yield payload
        time.sleep(SIMULATED_INTERVAL_SEC)


@app.route('/')
def index():
    """API root endpoint."""
    return jsonify({
        'name': 'Patient Security Management System API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'dashboard': '/dashboard',
            'sensor_data': '/api/sensor-data',
            'latest_data': '/api/latest-data',
            'alerts': '/api/alerts',
            'devices': '/api/devices',
            'statistics': '/api/statistics',
            'events': '/events'
        }
    })


@app.route('/dashboard')
def dashboard():
    """Serve the live dashboard UI."""
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/events')
def stream_events():
    """Stream simulated device payloads via Server-Sent Events."""

    def event_generator():
        for payload in generate_device_stream():
            yield f"data: {json.dumps(payload)}\n\n"

    headers = {
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    }
    return Response(event_generator(), mimetype='text/event-stream', headers=headers)


@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """
    Receive sensor data from ESP8266 devices.
    
    Expected JSON format:
    {
        "device_id": "ESP8266_PSMS_001",
        "location": "Room_101",
        "timestamp": 123456789,
        "sensors": {
            "temperature": 25.3,
            "humidity": 55.0,
            "air_quality": 342,
            "distance": 150
        },
        "alert_type": "none",
        "alert_active": false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['device_id', 'sensors']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Save to database
        record_id = save_sensor_data(data)
        
        # Sync to cloud if enabled
        if CLOUD_SYNC_ENABLED:
            try:
                from cloud_integration import sync_to_firestore
                sync_to_firestore(record_id, data)
            except Exception as e:
                logger.error(f"Cloud sync failed: {e}")
        
        response = {
            'status': 'success',
            'message': 'Sensor data received and stored',
            'record_id': record_id,
            'alert_active': data.get('alert_active', False)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/latest-data', methods=['GET'])
def get_latest_data():
    """Get latest sensor data for all devices or a specific device."""
    device_id = request.args.get('device_id')
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if device_id:
            cursor.execute('''
                SELECT * FROM sensor_data
                WHERE device_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (device_id,))
        else:
            cursor.execute('''
                SELECT s.* FROM sensor_data s
                INNER JOIN (
                    SELECT device_id, MAX(timestamp) as max_time
                    FROM sensor_data
                    GROUP BY device_id
                ) latest ON s.device_id = latest.device_id 
                    AND s.timestamp = latest.max_time
                ORDER BY s.timestamp DESC
            ''')
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        return jsonify({
            'status': 'success',
            'count': len(data),
            'data': data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving latest data: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get active or all alerts."""
    active_only = request.args.get('active', 'true').lower() == 'true'
    device_id = request.args.get('device_id')
    limit = int(request.args.get('limit', 100))
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        query = 'SELECT * FROM alerts WHERE 1=1'
        params = []
        
        if active_only:
            query += ' AND resolved = 0'
        
        if device_id:
            query += ' AND device_id = ?'
            params.append(device_id)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        alerts = [dict(row) for row in rows]
        
        return jsonify({
            'status': 'success',
            'count': len(alerts),
            'alerts': alerts
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get list of all registered devices."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT d.*,
                   COUNT(s.id) as total_readings,
                   MAX(s.timestamp) as last_reading
            FROM devices d
            LEFT JOIN sensor_data s ON d.device_id = s.device_id
            GROUP BY d.device_id
            ORDER BY d.last_seen DESC
        ''')
        
        rows = cursor.fetchall()
        devices = [dict(row) for row in rows]
        
        return jsonify({
            'status': 'success',
            'count': len(devices),
            'devices': devices
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving devices: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Total readings
        cursor.execute('SELECT COUNT(*) FROM sensor_data')
        total_readings = cursor.fetchone()[0]
        
        # Total devices
        cursor.execute('SELECT COUNT(*) FROM devices')
        total_devices = cursor.fetchone()[0]
        
        # Active alerts
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE resolved = 0')
        active_alerts = cursor.fetchone()[0]
        
        # Readings by device
        cursor.execute('''
            SELECT device_id, location, COUNT(*) as count
            FROM sensor_data
            GROUP BY device_id
            ORDER BY count DESC
        ''')
        readings_by_device = [
            {'device_id': row[0], 'location': row[1], 'count': row[2]}
            for row in cursor.fetchall()
        ]
        
        stats = {
            'status': 'success',
            'statistics': {
                'total_readings': total_readings,
                'total_devices': total_devices,
                'active_alerts': active_alerts,
                'readings_by_device': readings_by_device
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cloud_sync': CLOUD_SYNC_ENABLED
    }), 200


# Ensure database tables exist when the app module is imported
init_database()


if __name__ == '__main__':
    # Run Flask app
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting PSMS Server on {host}:{port}")
    logger.info(f"Cloud sync: {'enabled' if CLOUD_SYNC_ENABLED else 'disabled'}")
    
    app.run(host=host, port=port, debug=debug)
