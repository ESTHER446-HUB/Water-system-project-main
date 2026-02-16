"""
Hardware Integration Module for Raspberry Pi GPIO
Includes soil moisture sensors, water pumps, and camera monitoring
"""

try:
    import RPi.GPIO as GPIO
    import Adafruit_DHT
    from picamera import PiCamera
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

import time
from datetime import datetime

class SoilMoistureSensor:
    def __init__(self, pin, adc_channel=0):
        self.pin = pin
        self.adc_channel = adc_channel
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN)
    
    def read_moisture(self):
        """Read moisture from capacitive sensor (0-100%)"""
        if GPIO_AVAILABLE:
            try:
                import spidev
                spi = spidev.SpiDev()
                spi.open(0, 0)
                spi.max_speed_hz = 1350000
                
                adc = spi.xfer2([1, (8 + self.adc_channel) << 4, 0])
                data = ((adc[1] & 3) << 8) + adc[2]
                
                moisture = self._convert_to_percentage(data)
                spi.close()
                return moisture
            except:
                return self._simulate_reading()
        else:
            return self._simulate_reading()
    
    def _simulate_reading(self):
        import random
        return random.uniform(30, 80)
    
    def _convert_to_percentage(self, raw_value):
        """Convert raw ADC value to moisture percentage"""
        dry_value = 1023
        wet_value = 300
        
        moisture = 100 - ((raw_value - wet_value) / (dry_value - wet_value) * 100)
        return max(0, min(100, moisture))

class WaterPump:
    def __init__(self, pin):
        self.pin = pin
        self.is_running = False
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
    
    def activate(self, duration_seconds):
        """Activate pump for specified duration"""
        if GPIO_AVAILABLE:
            self.is_running = True
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration_seconds)
            GPIO.output(self.pin, GPIO.LOW)
            self.is_running = False
        else:
            time.sleep(duration_seconds)
    
    def stop(self):
        """Emergency stop"""
        if GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.LOW)
        self.is_running = False

class PlantCamera:
    def __init__(self):
        self.camera = None
        if GPIO_AVAILABLE:
            try:
                self.camera = PiCamera()
                self.camera.resolution = (1024, 768)
            except:
                pass
    
    def capture_image(self, sensor_id, save_path='static/images'):
        """Capture plant image"""
        if self.camera:
            filename = f'{save_path}/sensor_{sensor_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
            self.camera.capture(filename)
            return filename
        return None
    
    def start_timelapse(self, interval_minutes=60):
        """Start timelapse monitoring"""
        pass
    
    def close(self):
        if self.camera:
            self.camera.close()

class TemperatureHumiditySensor:
    def __init__(self, pin, sensor_type=Adafruit_DHT.DHT22):
        self.pin = pin
        self.sensor_type = sensor_type
    
    def read(self):
        """Read temperature and humidity"""
        if GPIO_AVAILABLE:
            try:
                humidity, temperature = Adafruit_DHT.read_retry(self.sensor_type, self.pin)
                return {'temperature': temperature, 'humidity': humidity}
            except:
                return self._simulate()
        else:
            return self._simulate()
    
    def _simulate(self):
        import random
        return {
            'temperature': random.uniform(20, 30),
            'humidity': random.uniform(40, 70)
        }

def cleanup():
    """Cleanup GPIO on exit"""
    if GPIO_AVAILABLE:
        GPIO.cleanup()

# Pin configuration
SENSOR_PINS = {
    1: {'gpio': 17, 'adc': 0},
    2: {'gpio': 27, 'adc': 1},
    3: {'gpio': 22, 'adc': 2},
    4: {'gpio': 10, 'adc': 3},
    5: {'gpio': 9, 'adc': 4}
}

PUMP_PINS = {
    1: 23,
    2: 24,
    3: 25,
    4: 8,
    5: 7
}

DHT_PIN = 4

# Initialize hardware
def init_hardware():
    sensors = {}
    pumps = {}
    
    for sensor_id, config in SENSOR_PINS.items():
        sensors[sensor_id] = SoilMoistureSensor(config['gpio'], config['adc'])
    
    for pump_id, pin in PUMP_PINS.items():
        pumps[pump_id] = WaterPump(pin)
    
    camera = PlantCamera()
    temp_sensor = TemperatureHumiditySensor(DHT_PIN)
    
    return sensors, pumps, camera, temp_sensor
