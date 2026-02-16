from flask import Flask, jsonify, request, send_from_directory, session, Response
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import threading
import time
import requests
import smtplib
from email.mime.text import MIMEText
import csv
import io
import hashlib
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key-change-in-production'
CORS(app)

DB_NAME = 'irrigation.db'
auto_mode = False
auto_thread = None

def get_db():
    conn = sqlite3.connect(DB_NAME)
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
        current_moisture REAL,
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
        timestamp TIMESTAMP,
        FOREIGN KEY(sensor_id) REFERENCES sensors(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY,
        sensor_id INTEGER,
        time TEXT NOT NULL,
        days TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        FOREIGN KEY(sensor_id) REFERENCES sensors(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        sensor_id INTEGER,
        message TEXT,
        timestamp TIMESTAMP,
        sent INTEGER DEFAULT 0,
        FOREIGN KEY(sensor_id) REFERENCES sensors(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    crops = [
        ('Tomato', 60, 80, 500, 'Requires consistent moisture'),
        ('Lettuce', 70, 85, 300, 'High water needs, shallow roots'),
        ('Carrot', 50, 70, 400, 'Moderate water, deep roots'),
        ('Pepper', 55, 75, 450, 'Moderate water needs'),
        ('Cucumber', 65, 80, 550, 'High water requirements'),
        ('Spinach', 65, 80, 350, 'Consistent moisture needed'),
        ('Beans', 55, 70, 400, 'Moderate water requirements'),
        ('Corn', 50, 70, 600, 'Deep roots, moderate water'),
        ('Strawberry', 60, 75, 300, 'Shallow roots, frequent water'),
        ('Herbs', 40, 60, 250, 'Low to moderate water needs')
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
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                 ('admin', pwd_hash, 'admin@irrigation.local'))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
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
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        lat, lon = request.args.get('lat', '0'), request.args.get('lon', '0')
        url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=precipitation_sum'
        response = requests.get(url, timeout=5)
        data = response.json()
        return jsonify({
            'temperature': data['current_weather']['temperature'],
            'precipitation': data['daily']['precipitation_sum'][0] if 'daily' in data else 0,
            'windspeed': data['current_weather']['windspeed']
        })
    except:
        return jsonify({'temperature': 25, 'precipitation': 0, 'windspeed': 5})

@app.route('/api/crops', methods=['GET'])
def get_crops():
    conn = get_db()
    crops = conn.execute('SELECT * FROM crops').fetchall()
    conn.close()
    return jsonify([dict(row) for row in crops])

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    conn = get_db()
    sensors = conn.execute('''
        SELECT s.*, c.name as crop_name, c.min_moisture, c.max_moisture, c.water_amount
        FROM sensors s
        LEFT JOIN crops c ON s.crop_id = c.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in sensors])

@app.route('/api/sensor/<int:sensor_id>/moisture', methods=['GET'])
def get_moisture(sensor_id):
    conn = get_db()
    sensor = conn.execute('SELECT * FROM sensors WHERE id = ?', (sensor_id,)).fetchone()
    
    if sensor:
        import random
        moisture = max(0, min(100, sensor['current_moisture'] + random.uniform(-2, -0.5)))
        
        conn.execute('UPDATE sensors SET current_moisture = ?, last_reading = ? WHERE id = ?',
                    (moisture, datetime.now(), sensor_id))
        conn.commit()
        
        result = {'sensor_id': sensor_id, 'moisture': round(moisture, 1), 'timestamp': datetime.now().isoformat()}
    else:
        result = {'error': 'Sensor not found'}
    
    conn.close()
    return jsonify(result)

@app.route('/api/sensor/<int:sensor_id>/water', methods=['POST'])
def water_plant(sensor_id):
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

@app.route('/api/auto-mode', methods=['GET', 'POST'])
def auto_mode_control():
    global auto_mode, auto_thread
    
    if request.method == 'POST':
        auto_mode = request.json.get('enabled', False)
        
        if auto_mode and (auto_thread is None or not auto_thread.is_alive()):
            auto_thread = threading.Thread(target=auto_watering_loop, daemon=True)
            auto_thread.start()
        
        return jsonify({'auto_mode': auto_mode})
    
    return jsonify({'auto_mode': auto_mode})

@app.route('/api/history/<int:sensor_id>', methods=['GET'])
def get_history(sensor_id):
    conn = get_db()
    logs = conn.execute('''
        SELECT * FROM watering_log
        WHERE sensor_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
    ''', (sensor_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in logs])

@app.route('/api/sensor/<int:sensor_id>/crop', methods=['PUT'])
def update_sensor_crop(sensor_id):
    crop_id = request.json.get('crop_id')
    conn = get_db()
    conn.execute('UPDATE sensors SET crop_id = ? WHERE id = ?', (crop_id, sensor_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/schedules', methods=['GET', 'POST'])
def manage_schedules():
    conn = get_db()
    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO schedules (sensor_id, time, days, active) VALUES (?, ?, ?, ?)',
                    (data['sensor_id'], data['time'], data['days'], 1))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    schedules = conn.execute('SELECT * FROM schedules WHERE active = 1').fetchall()
    conn.close()
    return jsonify([dict(row) for row in schedules])

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    conn = get_db()
    conn.execute('UPDATE schedules SET active = 0 WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/export/<int:sensor_id>', methods=['GET'])
def export_data(sensor_id):
    conn = get_db()
    logs = conn.execute('''SELECT * FROM watering_log WHERE sensor_id = ? ORDER BY timestamp DESC''',
                       (sensor_id,)).fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Moisture Before', 'Moisture After', 'Amount (ml)'])
    for log in logs:
        writer.writerow([log['timestamp'], log['moisture_before'], log['moisture_after'], log['amount']])
    
    return Response(output.getvalue(), mimetype='text/csv',
                   headers={'Content-Disposition': f'attachment;filename=sensor_{sensor_id}_history.csv'})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    conn = get_db()
    notifs = conn.execute('SELECT * FROM notifications ORDER BY timestamp DESC LIMIT 20').fetchall()
    conn.close()
    return jsonify([dict(row) for row in notifs])

def send_notification(sensor_id, message):
    conn = get_db()
    conn.execute('INSERT INTO notifications (sensor_id, message, timestamp) VALUES (?, ?, ?)',
                (sensor_id, message, datetime.now()))
    conn.commit()
    conn.close()

def auto_watering_loop():
    global auto_mode
    while auto_mode:
        conn = get_db()
        sensors = conn.execute('''
            SELECT s.*, c.min_moisture, c.water_amount, c.name as crop_name
            FROM sensors s
            LEFT JOIN crops c ON s.crop_id = c.id
        ''').fetchall()
        
        for sensor in sensors:
            if sensor['current_moisture'] < sensor['min_moisture']:
                moisture_before = sensor['current_moisture']
                moisture_increase = (sensor['water_amount'] / 100) * 15
                moisture_after = min(100, moisture_before + moisture_increase)
                
                conn.execute('UPDATE sensors SET current_moisture = ?, last_reading = ? WHERE id = ?',
                            (moisture_after, datetime.now(), sensor['id']))
                
                conn.execute('INSERT INTO watering_log (sensor_id, moisture_before, moisture_after, amount, timestamp) VALUES (?, ?, ?, ?, ?)',
                            (sensor['id'], moisture_before, moisture_after, sensor['water_amount'], datetime.now()))
                
                send_notification(sensor['id'], f"Auto-watered {sensor['crop_name']} - Moisture: {moisture_before:.1f}% → {moisture_after:.1f}%")
        
        conn.commit()
        conn.close()
        time.sleep(10)

def schedule_watering_loop():
    while True:
        conn = get_db()
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_day = now.strftime('%A')
        
        schedules = conn.execute('SELECT * FROM schedules WHERE active = 1').fetchall()
        
        for schedule in schedules:
            if schedule['time'] == current_time and current_day in schedule['days']:
                sensor = conn.execute('SELECT s.*, c.water_amount FROM sensors s LEFT JOIN crops c ON s.crop_id = c.id WHERE s.id = ?',
                                    (schedule['sensor_id'],)).fetchone()
                if sensor:
                    moisture_before = sensor['current_moisture']
                    moisture_increase = (sensor['water_amount'] / 100) * 15
                    moisture_after = min(100, moisture_before + moisture_increase)
                    
                    conn.execute('UPDATE sensors SET current_moisture = ?, last_reading = ? WHERE id = ?',
                                (moisture_after, datetime.now(), sensor['id']))
                    conn.execute('INSERT INTO watering_log (sensor_id, moisture_before, moisture_after, amount, timestamp) VALUES (?, ?, ?, ?, ?)',
                                (sensor['id'], moisture_before, moisture_after, sensor['water_amount'], datetime.now()))
        
        conn.commit()
        conn.close()
        time.sleep(60)

if __name__ == '__main__':
    init_db()
    schedule_thread = threading.Thread(target=schedule_watering_loop, daemon=True)
    schedule_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
