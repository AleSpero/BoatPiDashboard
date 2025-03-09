from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import sys
import os

# Add the core directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.sensor_monitor import SensorMonitorService
from core.gps_handler import GPSHandler

app = FastAPI(title="Boat Dashboard API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
monitor = SensorMonitorService()
gps = GPSHandler()  # You might need to adjust port/baud rate

@app.on_event("startup")
async def startup_event():
    """Start the services when the server starts"""
    monitor.start()
    gps.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the services when the server stops"""
    monitor.stop()
    gps.stop()

@app.get("/")
async def root():
    """Root endpoint returning API info"""
    return {
        "name": "Boat Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "sensors": "/sensors",
            "gps": "/gps"
        }
    }

@app.get("/sensors")
async def get_all_sensors():
    """Get latest readings from all sensors"""
    readings = monitor.get_all_readings()
    return {
        'timestamp': datetime.now().isoformat(),
        'sensors': {
            sensor: reading.value
            for sensor, reading in readings.items()
        }
    }

@app.get("/sensors/{sensor_name}")
async def get_sensor(sensor_name: str):
    """Get latest reading for a specific sensor"""
    if sensor_name not in monitor.available_sensors:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_name} not found")
    
    reading = monitor.get_reading(sensor_name)
    if reading is None:
        raise HTTPException(status_code=503, detail=f"No reading available for {sensor_name}")
    
    return {
        'timestamp': datetime.now().isoformat(),
        'sensor': sensor_name,
        'value': reading.value
    }

@app.get("/gps")
async def get_gps_data():
    """Get all GPS data"""
    data = gps.get_data()
    if not data:
        raise HTTPException(status_code=503, detail="GPS data not available")
    
    return {
        'timestamp': data.timestamp.isoformat(),
        'position': {
            'latitude': data.latitude,
            'longitude': data.longitude,
            'altitude': data.altitude
        },
        'navigation': {
            'speed_knots': data.speed_knots,
            'speed_kmh': data.speed_knots * 1.852,  # Convert knots to km/h
            'heading': data.heading
        },
        'status': {
            'satellites': data.satellites,
            'fix_quality': data.fix_quality,
            'valid': data.valid
        }
    }

@app.get("/gps/position")
async def get_gps_position():
    """Get GPS position data only"""
    data = gps.get_data()
    if not data:
        raise HTTPException(status_code=503, detail="GPS data not available")
    
    if not data.valid:
        raise HTTPException(status_code=503, detail="No valid GPS fix")
    
    return {
        'timestamp': data.timestamp.isoformat(),
        'latitude': data.latitude,
        'longitude': data.longitude,
        'altitude': data.altitude,
        'satellites': data.satellites
    }

@app.get("/gps/navigation")
async def get_gps_navigation():
    """Get GPS navigation data only (speed and heading)"""
    data = gps.get_data()
    if not data:
        raise HTTPException(status_code=503, detail="GPS data not available")
    
    if not data.valid:
        raise HTTPException(status_code=503, detail="No valid GPS fix")
    
    return {
        'timestamp': data.timestamp.isoformat(),
        'speed_knots': data.speed_knots,
        'speed_kmh': data.speed_knots * 1.852,
        'heading': data.heading
    }

@app.get("/status")
async def get_status():
    """Get system status including GPS and sensor status"""
    return {
        'sensors': {
            'status': 'running' if monitor._running else 'stopped',
            'refresh_rates': monitor.REFRESH_RATES,
            'available_sensors': monitor.available_sensors
        },
        'gps': {
            'status': 'running' if gps.is_running else 'stopped',
            'has_fix': gps.has_fix
        }
    }

def main():
    """Run the server"""
    uvicorn.run(
        "server:app",
        host="0.0.0.0",  # Make accessible from other devices
        port=8000,
        reload=True      # Auto-reload on code changes
    )

if __name__ == "__main__":
    main() 