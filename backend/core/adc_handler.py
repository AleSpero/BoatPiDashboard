import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from typing import Dict, Optional
import time

class ADCHandler:
    # ADS1115 specifications
    MAX_VOLTAGE = 5.240  # Maximum voltage of ADS1115
    MAX_VOLTAGE_FUEL_LEVEL = 2.77  # Maximum voltage of fuel level sensor
    
    # Conversion factors and calibration constants
    FUEL_LEVEL_FACTOR = 100.0 / MAX_VOLTAGE_FUEL_LEVEL  # Convert to percentage
    BATTERY_VOLTAGE_DIVIDER = 2.44275  # Voltage divider ratio for 12.8V max input
    TEMPERATURE_FACTOR = 100.0  # Temperature conversion factor
    RPM_FACTOR = 1000.0  # RPM conversion factor
    
    # Channel configurations
    CHANNELS = {
        'fuel_level': 0,    # A0
        'rpm': 1,           # A1
        'battery': 2,       # A2
        'temperature': 3    # A3
    }
    
    def __init__(self):
        print("Initializing ADC Handler...")
        try:
            # Initialize I2C bus
            print("Setting up I2C bus...")
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Initialize ADS1115
            print("Initializing ADS1115...")
            self.ads = ADS.ADS1115(i2c)
            print("ADS1115 initialized successfully")
            
            # Create analog input objects for each channel
            print("Setting up ADC channels...")
            self.channels = {}
            for name, channel in self.CHANNELS.items():
                print(f"  Initializing channel {name} on A{channel}...")
                self.channels[name] = AnalogIn(self.ads, getattr(ADS, f'P{channel}'))
            print("All channels initialized successfully")
            
            # Map conversion factors using class constants
            self.conversion_factors = {
                'fuel_level': self.FUEL_LEVEL_FACTOR,
                'battery': self.BATTERY_VOLTAGE_DIVIDER,
                'temperature': self.TEMPERATURE_FACTOR,
                'rpm': self.RPM_FACTOR
            }
            print("ADC Handler initialization complete")
            
        except Exception as e:
            print(f"Error initializing ADC Handler: {str(e)}")
            print("Make sure:")
            print("1. The ADS1115 is properly connected to the I2C pins")
            print("2. I2C is enabled on your device")
            print("3. You have the required permissions to access I2C")
            raise

    def read_raw(self, channel_name: str) -> Optional[float]:
        """Read raw voltage from specified channel."""
        if channel_name not in self.channels:
            return None
        return self.channels[channel_name].voltage

    def read_fuel_level(self) -> float:
        """Read fuel level as percentage (0-100%)."""
        raw_value = self.read_raw('fuel_level')
        if raw_value is None:
            return 0.0
        percentage = raw_value * self.conversion_factors['fuel_level']
        return min(max(percentage, 0.0), 100.0)

    def read_rpm(self) -> float:
        """Read engine RPM."""
        raw_value = self.read_raw('rpm')
        if raw_value is None:
            return 0.0
        return raw_value * self.conversion_factors['rpm']

    def read_battery_voltage(self) -> float:
        """Read battery voltage (considering voltage divider)."""
        raw_value = self.read_raw('battery')
        if raw_value is None:
            return 0.0
        return raw_value * self.conversion_factors['battery']

    def read_temperature(self) -> float:
        """Read engine temperature in Celsius."""
        raw_value = self.read_raw('temperature')
        if raw_value is None:
            return 0.0
        return raw_value * self.conversion_factors['temperature']

    def read_all(self) -> Dict[str, float]:
        """Read all sensors and return their converted values."""
        return {
            'fuel_level': self.read_fuel_level(),
            'rpm': self.read_rpm(),
            'battery': self.read_battery_voltage(),
            'temperature': self.read_temperature()
        } 