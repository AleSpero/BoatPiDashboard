from typing import Dict, Optional, List, Any
import threading
import time
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict
from adc_handler import ADCHandler
import json

@dataclass
class SensorReading:
    """Data class to hold a sensor reading with its timestamp"""
    value: float
    timestamp: float
    stale: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the reading to a dictionary"""
        return {
            'value': self.value,
            'timestamp': self.timestamp,
            'stale': self.stale,
            'age': time.time() - self.timestamp
        }

class SensorMonitorService:
    # Refresh intervals in seconds
    REFRESH_RATES = {
        'rpm': 0.1,        # 100ms - 10 times per second
        'battery': 1.0,    # 1 second
        'fuel_level': 2.0, # 2 seconds
        'temperature': 2.0  # 2 seconds
    }

    # Maximum age of cached values before considered stale
    MAX_AGE = {
        'rpm': 0.5,        # RPM data becomes stale after 500ms
        'battery': 5.0,    # Battery data becomes stale after 5s
        'fuel_level': 10.0, # Fuel level becomes stale after 10s
        'temperature': 10.0 # Temperature becomes stale after 10s
    }

    def __init__(self):
        """Initialize the sensor monitoring service"""
        self.adc = ADCHandler()
        self._readings: Dict[str, SensorReading] = {}
        self._lock = threading.Lock()
        self._running = False
        self._polling_thread: Optional[threading.Thread] = None
        self.last_read = defaultdict(float)

    def start(self):
        """Start the sensor polling thread"""
        if not self._running:
            self._running = True
            self._polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
            self._polling_thread.start()

    def stop(self):
        """Stop the sensor polling thread"""
        self._running = False
        if self._polling_thread:
            self._polling_thread.join()

    def _should_update(self, sensor: str) -> bool:
        """Check if it's time to update a specific sensor"""
        current_time = time.time()
        if current_time - self.last_read[sensor] >= self.REFRESH_RATES[sensor]:
            self.last_read[sensor] = current_time
            return True
        return False

    def _update_reading(self, sensor: str, value: float):
        """Update the reading for a sensor with current timestamp"""
        with self._lock:
            self._readings[sensor] = SensorReading(
                value=value,
                timestamp=time.time()
            )

    def _polling_loop(self):
        """Main polling loop that respects refresh rates"""
        while self._running:
            if self._should_update('rpm'):
                self._update_reading('rpm', self.adc.read_rpm())
            
            if self._should_update('battery'):
                self._update_reading('battery', self.adc.read_battery_voltage())
            
            if self._should_update('fuel_level'):
                self._update_reading('fuel_level', self.adc.read_fuel_level())
            
            if self._should_update('temperature'):
                self._update_reading('temperature', self.adc.read_temperature())
            
            # Sleep for the shortest refresh interval
            time.sleep(min(self.REFRESH_RATES.values()))

    def get_reading(self, sensor: str) -> Optional[SensorReading]:
        """Get the latest reading for a specific sensor"""
        with self._lock:
            reading = self._readings.get(sensor)
            if reading is None:
                return None
            
            # Check if reading is stale
            age = time.time() - reading.timestamp
            reading.stale = age > self.MAX_AGE[sensor]
            return reading

    def get_reading_dict(self, sensor: str) -> Optional[Dict[str, Any]]:
        """Get the latest reading for a sensor as a dictionary"""
        reading = self.get_reading(sensor)
        return reading.to_dict() if reading else None

    def get_all_readings(self) -> Dict[str, SensorReading]:
        """Get all latest readings"""
        with self._lock:
            current_time = time.time()
            readings = {}
            for sensor in self.REFRESH_RATES.keys():
                reading = self._readings.get(sensor)
                if reading:
                    # Check if reading is stale
                    age = current_time - reading.timestamp
                    reading.stale = age > self.MAX_AGE[sensor]
                    readings[sensor] = reading
            return readings

    def get_all_readings_dict(self) -> Dict[str, Dict[str, Any]]:
        """Get all latest readings as a dictionary suitable for JSON conversion"""
        readings = self.get_all_readings()
        return {
            sensor: reading.to_dict()
            for sensor, reading in readings.items()
        }

    def get_latest_values_dict(self) -> Dict[str, Any]:
        """Get a simple dictionary with just the latest values"""
        readings = self.get_all_readings()
        return {
            'timestamp': time.time(),
            'values': {
                sensor: reading.value
                for sensor, reading in readings.items()
            },
            'stale_sensors': [
                sensor
                for sensor, reading in readings.items()
                if reading.stale
            ]
        }

    @property
    def available_sensors(self) -> List[str]:
        """List all available sensors"""
        return list(self.REFRESH_RATES.keys()) 