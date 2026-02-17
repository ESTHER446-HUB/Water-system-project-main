from flask import Flask, jsonify, request, send_from_directory, session, Response
from flask_cors import CORS
import sqlite3
from datetime import datetime
import threading
import time
import csv
import io
import hashlib
import os
import random

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
CORS(app)

DB_NAME = 'irrigation.db'
auto_mode = False
auto_thread = None

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS crops (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        min_moisture INTEGER NOT NULL,
        max_moisture INTEGER NOT NULL,
        water_amount INTEGER NOT NULL,
        description TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sensors (
        id INTEGER PRIMARY KEY,
        crop_id INTEGER,
        current_moisture REAL DEFAULT 50.0,
        pin INTEGER,
        last_reading TIMESTAMP,
        FOREIGN KEY(crop_id) REFERENCES crops(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS watering_log (
        id INTEGER PRIMARY KEY,
        sensor_id INTEGER,
        moisture_before REAL,
        moisture_after REAL,
        amount INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(sensor_id) REFERENCES sensors(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY,
        sensor_id INTEGER,
        time TEXT NOT NULL,
        days TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        FOREIGN KEY(sensor_id) REFERENCES sensors(id)
    )''')
    
    crops = [
        ('Tomato', 60, 80, 500, 'Consistent moisture'),
        ('Lettuce', 70, 85, 300, 'High water needs'),
        ('Carrot', 50, 70, 400, 'Moderate water'),
        ('Pepper', 55, 75, 450, 'Moderate needs'),
        ('Cucumber', 65, 80, 550, 'High water'),
        ('Spinach', 65, 80, 350, 'Consistent moisture'),
        ('Beans', 55, 70, 400, 'Moderate water'),
        ('Corn', 50, 70, 600, 'Deep roots'),
        ('Strawberry', 60, 75, 300, 'Frequent water'),
        ('Herbs', 40, 60, 250, 'Low water needs')
    ]
    
    for crop in crops:
        c.execute('INSERT OR IGNORE INTO crops (name, min_moisture, max_moisture, water_amount, description) VALUES (?, ?, ?, ?, ?)', crop)
    
    c.execute('SELECT COUNT(*) FROM sensors')
    if c.fetchone()[0] == 0:
        for i in range(1, 6):
            c.execute('INSERT INTO sensors (crop_id, current_moisture, pin, last_reading) VALUES (?, ?, ?, ?)',
                     (i, 50.0, i, datetime.now()))
    
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        pwd_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', pwd_hash))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = hashlib.sha256(data.get('password', '').encode()).hexdigest()
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'username': user['username']})
        return jsonify({'success': False}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/crops', methods=['GET'])
def get_crops():
    try:
        conn = get_db()
        crops = conn.execute('SELECT * FROM crops ORDER BY name').fetchall()
        conn.close()
        return jsonify([dict(row) for row in crops])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    try:
        conn = get_db()
        sensors = conn.execute('''
            SELECT s.*, c.name as crop_name, c.min_moisture, c.max_moisture, c.water_amount, c.description
            FROM sensors s
            LEFT JOIN crops c ON s.crop_id = c.id
            ORDER BY s.id
        ''').fetchall()
        conn.close()
        return jsonify([dict(row) for row in sensors])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/<int:sensor_id>/moisture', methods=['GET'])
def get_moisture(sensor_id):
    try:
        conn = get_db()
        sensor = conn.execute('SELECT * FROM sensors WHERE id = ?', (sensor_id,)).fetchone()
        
        if not sensor:
            conn.close()
            return jsonify({'error': 'Sensor not found'}), 404
        
        moisture = max(0, min(100, sensor['current_moisture'] + random.uniform(-2, -0.5)))
        
        conn.execute('UPDATE sensors SET current_moisture = ?, last_reading = ? WHERE id = ?',
                    (moisture, datetime.now(), sensor_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'sensor_id': sensor_id,
            'moisture': round(moisture, 1),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/<int:sensor_id>/water', methods=['POST'])
def water_plant(sensor_id):
    try:
        conn = get_db()
        sensor = conn.execute('''
            SELECT s.*, c.water_amount, c.max_moisture
            FROM sensors s
            LEFT JOIN crops c ON s.crop_id = c.id
            WHERE s.id = ?
        ''', (sensor_id,)).fetchone()
        
        if not sensor:
            conn.close()
            return jsonify({'error': 'Sensor not found'}), 404
        
        moisture_before = sensor['current_moisture']
        amount = sensor['water_amount']
        moisture_increase = (amount / 100) * 15
        moisture_after = min(sensor['max_moisture'], moisture_before + moisture_increase)
        
        conn.execute('UPDATE sensors SET current_moisture = ?, last_reading = ? WHERE id = ?',
                    (moisture_after, datetime.now(), sensor_id))
        
        conn.execute('INSERT INTO watering_log (sensor_id, moisture_before, moisture_after, amount, timestamp) VALUES (?, ?, ?, ?, ?)',
                    (sensor_id, moisture_before, moisture_after, amount, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'moisture_before': round(moisture_before, 1),
            'moisture_after': round(moisture_after, 1),
            'amount': amount
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-mode', methods=['GET', 'POST'])
def auto_mode_control():
    global auto_mode, auto_thread
    
    try:
        if request.method == 'POST':
            auto_mode = request.json.get('enabled', False)
            
            if auto_mode and (auto_thread is None or not auto_thread.is_alive()):
                auto_thread = threading.Thread(target=auto_watering_loop, daemon=True)
                auto_thread.start()
            
            return jsonify({'auto_mode': auto_mode})
        
        return jsonify({'auto_mode': auto_mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<int:sensor_id>', methods=['GET'])
def get_history(sensor_id):
    try:
        conn = get_db()
        logs = conn.execute('''
            SELECT * FROM watering_log
            WHERE sensor_id = ?
            ORDER BY timestamp DESC
            LIMIT 50
        ''', (sensor_id,)).fetchall()
        conn.close()
        return jsonify([dict(row) for row in logs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/<int:sensor_id>/crop', methods=['PUT'])
def update_sensor_crop(sensor_id):
    try:
        crop_id = request.json.get('crop_id')
        conn = get_db()
        conn.execute('UPDATE sensors SET crop_id = ? WHERE id = ?', (crop_id, sensor_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules', methods=['GET', 'POST'])
def manage_schedules():
    try:
        conn = get_db()
        if request.method == 'POST':
            data = request.json
            conn.execute('INSERT INTO schedules (sensor_id, time, days, active) VALUES (?, ?, ?, ?)',
                        (data['sensor_id'], data['time'], data['days'], 1))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        
        schedules = conn.execute('SELECT * FROM schedules WHERE active = 1 ORDER BY time').fetchall()
        conn.close()
        return jsonify([dict(row) for row in schedules])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    try:
        conn = get_db()
        conn.execute('UPDATE schedules SET active = 0 WHERE id = ?', (schedule_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<int:sensor_id>', methods=['GET'])
def export_data(sensor_id):
    try:
        conn = get_db()
        logs = conn.execute('SELECT * FROM watering_log WHERE sensor_id = ? ORDER BY timestamp DESC',
                           (sensor_id,)).fetchall()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Moisture Before (%)', 'Moisture After (%)', 'Amount (ml)'])
        for log in logs:
            writer.writerow([log['timestamp'], log['moisture_before'], log['moisture_after'], log['amount']])
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=sensor_{sensor_id}_data.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db()
        
        sensors = conn.execute('SELECT AVG(current_moisture) as avg, COUNT(*) as total FROM sensors').fetchone()
        today_watering = conn.execute('''
            SELECT COUNT(*) as count FROM watering_log 
            WHERE DATE(timestamp) = DATE('now')
        ''').fetchone()
        
        conn.close()
        
        return jsonify({
            'avg_moisture': round(sensors['avg'], 1) if sensors['avg'] else 0,
            'total_sensors': sensors['total'],
            'today_watering': today_watering['count']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def auto_watering_loop():
    global auto_mode
    while auto_mode:
        try:
            conn = get_db()
            sensors = conn.execute('''
                SELECT s.*, c.min_moisture, c.water_amount, c.max_moisture
                FROM sensors s
                LEFT JOIN crops c ON s.crop_id = c.id
            ''').fetchall()
            
            for sensor in sensors:
                if sensor['current_moisture'] < sensor['min_moisture']:
                    moisture_before = sensor['current_moisture']
                    moisture_increase = (sensor['water_amount'] / 100) * 15
                    moisture_after = min(sensor['max_moisture'], moisture_before + moisture_increase)
                    
                    conn.execute('UPDATE sensors SET current_moisture = ?, last_reading = ? WHERE id = ?',
                                (moisture_after, datetime.now(), sensor['id']))
                    
                    conn.execute('INSERT INTO watering_log (sensor_id, moisture_before, moisture_after, amount, timestamp) VALUES (?, ?, ?, ?, ?)',
                                (sensor['id'], moisture_before, moisture_after, sensor['water_amount'], datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Auto watering error: {e}")
        
        time.sleep(30)

def schedule_watering_loop():
    while True:
        try:
            conn = get_db()
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            current_day = now.strftime('%A')
            
            schedules = conn.execute('SELECT * FROM schedules WHERE active = 1').fetchall()
            
            for schedule in schedules:
                if schedule['time'] == current_time and current_day in schedule['days']:
                    sensor = conn.execute('''
                        SELECT s.*, c.water_amount, c.max_moisture 
                        FROM sensors s 
                        LEFT JOIN crops c ON s.crop_id = c.id 
                        WHERE s.id = ?
                    ''', (schedule['sensor_id'],)).fetchone()
                    
                    if sensor:
                        moisture_before = sensor['current_moisture']
                        moisture_increase = (sensor['water_amount'] / 100) * 15
                        moisture_after = min(sensor['max_moisture'], moisture_before + moisture_increase)
                        
                        conn.execute('UPDATE sensors SET current_moisture = ?, last_reading = ? WHERE id = ?',
                                    (moisture_after, datetime.now(), sensor['id']))
                        conn.execute('INSERT INTO watering_log (sensor_id, moisture_before, moisture_after, amount, timestamp) VALUES (?, ?, ?, ?, ?)',
                                    (sensor['id'], moisture_before, moisture_after, sensor['water_amount'], datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Schedule watering error: {e}")
        
        time.sleep(60)

if __name__ == '__main__':
    init_db()
    schedule_thread = threading.Thread(target=schedule_watering_loop, daemon=True)
    schedule_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
