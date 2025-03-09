#!/usr/bin/env python3

from adc_handler import ADCHandler
import time
from datetime import datetime
import sys
import signal

def clear_line():
    """Clear the current line in the terminal."""
    sys.stdout.write('\033[K')  # Clear line
    sys.stdout.write('\033[F')  # Move cursor up

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
        adc = ADCHandler()
        print("\nStarting sensor polling (Press Ctrl+C to exit)...\n")
        print(adc.channels)
        
        # Print header
        print("Time       | Fuel Level | RPM    | Battery | Temperature")
        print("-" * 55)
        
        # Add empty lines that will be updated
        print("\n" * 4)
        
        while True:
            # Move cursor up to overwrite previous values
            sys.stdout.write('\033[4F')
            
            # Get all sensor readings
            readings = adc.read_all()
            
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
            
            #print(output)
            
            # Print raw voltages for debugging
            raw_values = {name: adc.read_raw(name) for name in adc.CHANNELS.keys()}
            print(f"Raw voltages: " + " | ".join(f"{k}: {v:.3f}V" for k, v in raw_values.items()))
            
            # Add empty lines to maintain consistent display
            print("\n" * 2)
            
            time.sleep(1)  # Update every second
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 