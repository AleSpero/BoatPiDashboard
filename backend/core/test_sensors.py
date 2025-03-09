#!/usr/bin/env python3

from adc_handler import ADCHandler
import time
from datetime import datetime
import sys
import signal
from typing import Dict
from collections import defaultdict

class SensorMonitor:
    # Refresh intervals in seconds
    REFRESH_RATES = {
        'rpm': 0.1,        # 100ms - 10 times per second
        'battery': 1.0,    # 1 second
        'fuel_level': 2.0, # 2 seconds
        'temperature': 2.0 # 2 seconds
    }

    def __init__(self):
        self.adc = ADCHandler()
        self.last_read = defaultdict(float)
        self.values = defaultdict(float)

    def should_update(self, sensor: str) -> bool:
        """Check if it's time to update a specific sensor."""
        current_time = time.time()
        if current_time - self.last_read[sensor] >= self.REFRESH_RATES[sensor]:
            self.last_read[sensor] = current_time
            return True
        return False

    def update_sensors(self) -> Dict[str, float]:
        """Update sensor values based on their refresh rates."""
        if self.should_update('rpm'):
            self.values['rpm'] = self.adc.read_rpm()
        
        if self.should_update('battery'):
            self.values['battery'] = self.adc.read_battery_voltage()
        
        if self.should_update('fuel_level'):
            self.values['fuel_level'] = self.adc.read_fuel_level()
        
        if self.should_update('temperature'):
            self.values['temperature'] = self.adc.read_temperature()
        
        return dict(self.values)

def format_value(name: str, value: float) -> str:
    """Format sensor values with appropriate units."""
    if name == 'fuel_level':
        return f"{value:.1f}%"
    elif name == 'rpm':
        return f"{value:.0f} RPM"
    elif name == 'battery':
        return f"{value:.2f}V"
    elif name == 'temperature':
        return f"{value:.1f}°C"
    return f"{value:.2f}"

def main():
    # Setup signal handler for clean exit
    def signal_handler(sig, frame):
        print("\n\nExiting...\n")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        monitor = SensorMonitor()
        print("\nStarting sensor polling (Press Ctrl+C to exit)...\n")
        
        # Print header
        print("Time       | Fuel Level | RPM    | Battery | Temperature")
        print("-" * 55)
        
        # Add empty lines that will be updated
        print("\n" * 4)
        
        while True:
            # Move cursor up to overwrite previous values
            sys.stdout.write('\033[4F')
            
            # Get all sensor readings
            readings = monitor.update_sensors()
            
            # Format current time
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Format and display the readings
            output = (
                f"{current_time} | "
                f"{format_value('fuel_level', readings['fuel_level']):^10} | "
                f"{format_value('rpm', readings['rpm']):^6} | "
                f"{format_value('battery', readings['battery']):^7} | "
                f"{format_value('temperature', readings['temperature']):^11}"
            )
            
            print(output)
            
            # Print raw voltages for debugging
            raw_values = {name: monitor.adc.read_raw(name) for name in monitor.adc.CHANNELS.keys()}
            print(f"Raw voltages: " + " | ".join(f"{k}: {v:.3f}V" for k, v in raw_values.items()))
            
            # Add empty lines to maintain consistent display
            print("\n" * 2)
            
            # Sleep for the shortest refresh interval
            time.sleep(min(monitor.REFRESH_RATES.values()))
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 