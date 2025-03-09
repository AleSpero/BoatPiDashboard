#!/usr/bin/env python3

from sensor_monitor import SensorMonitorService
import time
import signal
import sys
from datetime import datetime

def format_reading(name: str, reading):
    """Format sensor reading with appropriate units"""
    if reading is None:
        return "N/A"
    
    value = reading.value
    stale = " (stale)" if reading.stale else ""
    
    if name == 'fuel_level':
        return f"{value:.1f}%{stale}"
    elif name == 'rpm':
        return f"{value:.0f} RPM{stale}"
    elif name == 'battery':
        return f"{value:.2f}V{stale}"
    elif name == 'temperature':
        return f"{value:.1f}°C{stale}"
    return f"{value:.2f}{stale}"

def main():
    def signal_handler(sig, frame):
        print("\n\nStopping sensor monitor...\n")
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        monitor = SensorMonitorService()
        print("\nStarting sensor monitor (Press Ctrl+C to exit)...\n")
        monitor.start()
        
        # Print header
        print("Time       | Fuel Level | RPM    | Battery | Temperature")
        print("-" * 55)
        
        # Add empty lines that will be updated
        print("\n" * 4)
        
        while True:
            # Move cursor up to overwrite previous values
            sys.stdout.write('\033[4F')
            
            # Get all readings
            readings = monitor.get_all_readings()
            
            # Format current time
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Format and display the readings
            output = (
                f"{current_time} | "
                f"{format_reading('fuel_level', readings.get('fuel_level')):^10} | "
                f"{format_reading('rpm', readings.get('rpm')):^6} | "
                f"{format_reading('battery', readings.get('battery')):^7} | "
                f"{format_reading('temperature', readings.get('temperature')):^11}"
            )
            
            print(output)
            
            # Print raw timestamps for debugging
            timestamps = {name: f"{time.time() - r.timestamp:.1f}s ago" 
                        for name, r in readings.items()}
            print("Ages: " + " | ".join(f"{k}: {v}" for k, v in timestamps.items()))
            
            # Add empty lines to maintain consistent display
            print("\n" * 2)
            
            # Update display every 100ms
            time.sleep(0.1)
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 