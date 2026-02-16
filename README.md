# Smart Irrigation System

Full-stack multi-crop water management system.

## Features

- Multi-Crop Support: 10 crops with specific water needs
- Real-time Monitoring: Live moisture readings from 5 sensors
- Auto/Manual Control: Automated watering based on thresholds
- Web Dashboard: Modern responsive UI
- Hardware Ready: GPIO integration for Raspberry Pi
- Weather Integration: Real-time weather data
- User Authentication: Secure login system
- Scheduling: Automatic watering schedules
- Notifications: Real-time alerts
- Data Export: Download history as CSV
- Camera Integration: Plant monitoring

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

Login: `admin` / `admin123`

## Project Structure

```
├── app.py              # Flask backend
├── hardware.py         # GPIO sensors
├── static/
│   ├── index.html      # Dashboard
│   ├── style.css       # Styling
│   └── app.js          # Frontend logic
└── requirements.txt    # Dependencies
```

## Deploy to Render

1. Push to GitHub
2. Go to render.com
3. New Web Service → Connect repo
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
6. Deploy!

## Hardware Setup

- Sensors: GPIO 17, 27, 22, 10, 9
- Pumps: GPIO 23, 24, 25, 8, 7
- DHT22: GPIO 4
- Camera: CSI port

## Crops

Tomato, Lettuce, Carrot, Pepper, Cucumber, Spinach, Beans, Corn, Strawberry, Herbs

## Author

Esther Kuria
