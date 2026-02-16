# Smart Irrigation System v3.0

Full-stack multi-crop water management system with hardware sensor integration.

## Features

- **Multi-Crop Support**: 10 pre-configured crops with specific water needs
- **Real-time Monitoring**: Live moisture readings from 5 sensors
- **Auto/Manual Control**: Automated watering based on crop thresholds
- **Web Dashboard**: Modern responsive UI for monitoring and control
- **Hardware Ready**: GPIO integration for Raspberry Pi sensors
- **Historical Data**: Complete watering logs and analytics
- **Weather Integration**: Real-time weather data affects watering decisions
- **User Authentication**: Secure login system (admin/admin123)
- **Scheduling**: Set automatic watering schedules by time and day
- **Notifications**: Real-time alerts for watering events
- **Data Export**: Download watering history as CSV
- **Camera Integration**: Plant monitoring with Pi Camera

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python app.py
```

3. Open browser:
```
http://localhost:5000
```

## Project Structure

```
├── app.py              # Flask backend API
├── hardware.py         # GPIO sensor integration
├── static/
│   ├── index.html      # Frontend dashboard
│   ├── style.css       # Styling
│   └── app.js          # Frontend logic
├── irrigation.db       # SQLite database
└── requirements.txt    # Dependencies
```

## API Endpoints

- POST `/api/login` - User authentication
- POST `/api/logout` - Logout user
- GET `/api/weather` - Get weather data
- GET `/api/crops` - List all crops
- GET `/api/sensors` - Get all sensors
- GET `/api/sensor/<id>/moisture` - Read moisture
- POST `/api/sensor/<id>/water` - Water plant
- PUT `/api/sensor/<id>/crop` - Change crop type
- POST `/api/auto-mode` - Toggle auto mode
- GET `/api/history/<id>` - Watering history
- GET `/api/export/<id>` - Export data as CSV
- GET/POST `/api/schedules` - Manage schedules
- DELETE `/api/schedules/<id>` - Delete schedule
- GET `/api/notifications` - Get notifications

## Hardware Setup

Connect sensors to GPIO pins (see hardware.py):
- Sensors 1-5: GPIO 17, 27, 22, 10, 9 (with ADC channels 0-4)
- Pumps 1-5: GPIO 23, 24, 25, 8, 7
- DHT22 Temp/Humidity: GPIO 4
- Pi Camera: CSI port

## Crops Included

1. Tomato (60-80% moisture)
2. Lettuce (70-85% moisture)
3. Carrot (50-70% moisture)
4. Pepper (55-75% moisture)
5. Cucumber (65-80% moisture)
6. Spinach (65-80% moisture)
7. Beans (55-70% moisture)
8. Corn (50-70% moisture)
9. Strawberry (60-75% moisture)
10. Herbs (40-60% moisture)

## Default Login

- Username: `admin`
- Password: `admin123`

## Features in Detail

### Weather Integration
Automatically fetches local weather data using Open-Meteo API. Displays temperature, precipitation, and wind speed.

### Scheduling System
Set specific times and days for automatic watering. Example: Water every Monday and Thursday at 7:00 AM.

### Notifications
Receive alerts when plants are watered automatically or when moisture levels are critical.

### Data Export
Export complete watering history for any sensor as CSV for analysis in Excel or other tools.

### Camera Monitoring
Capture plant images for visual monitoring and growth tracking (requires Pi Camera).

## Author

Esther Kuria
