"""
Sensor data store — simulates ESP32 sensor node data.
In production, this would read from MQTT/InfluxDB.
For now it holds realistic simulated data that updates on each read.
"""

import random, math
from datetime import datetime


class SensorStore:
    def __init__(self):
        self.pump_running = False
        self.pump_start_time = None
        self.water_usage_7d = [35, 50, 30, 45, 25, 60, 0]  # liters, last is today
        self.last_hardware_data = None
        self.nodes = [
            {"id": "alpha", "name": "Node Alpha", "location": "North Field Sector",
             "battery": 82, "signal": "Strong", "signal_color": "#2E7D32", "online": True},
            {"id": "beta", "name": "Node Beta", "location": "East Orchard",
             "battery": 24, "signal": "Good", "signal_color": "#2E7D32", "online": True},
        ]

    def get_live_telemetry(self) -> dict:
        """Return sensor readings, using hardware data if available, else mock."""
        hour = datetime.now().hour
        
        # Base values
        if self.last_hardware_data:
            moisture = self.last_hardware_data.get("Moisture", 75)
            n = self.last_hardware_data.get("N", 45)
            p = self.last_hardware_data.get("P", 30)
            k = self.last_hardware_data.get("K", 25)
            ph = self.last_hardware_data.get("ph", 6.5)
            temp = self.last_hardware_data.get("temperature", 25.0)
            humidity = self.last_hardware_data.get("humidity", 65.0)
        else:
            base_temp = 25 + 8 * math.sin((hour - 6) * math.pi / 12)
            base_humidity = 65 - 15 * math.sin((hour - 6) * math.pi / 12)
            moisture = max(10, min(95, 75 + random.randint(-10, 5)))
            n = max(20, 45 + random.randint(-5, 5))
            p = max(15, 30 + random.randint(-3, 3))
            k = max(10, 25 + random.randint(-3, 3))
            ph = round(6.5 + random.uniform(-0.3, 0.3), 1)
            temp = round(base_temp + random.uniform(-1, 1), 1)
            humidity = round(base_humidity + random.uniform(-3, 3), 1)

        moisture_status = "Optimal" if moisture > 50 else ("Low" if moisture > 25 else "Critical")
        ph_status = "Optimal" if 6.0 <= ph <= 7.5 else ("Acidic" if ph < 6.0 else "Alkaline")

        # Drain battery slowly
        for node in self.nodes:
            node["battery"] = max(5, node["battery"] - random.randint(0, 1))

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "soil_moisture": {"value": moisture, "status": moisture_status},
            "npk": {"N": n, "P": p, "K": k},
            "ph": {"value": ph, "status": ph_status},
            "temperature": temp,
            "humidity": humidity,
            "nodes": self.nodes,
            "raw_sensors": {
                "N": n, "P": p, "K": k,
                "temperature": temp, "humidity": humidity,
                "ph": ph, "rainfall": round(random.uniform(0, 5), 1),
                "Moisture": moisture,
            },
        }

    def get_irrigation_status(self) -> dict:
        """Get irrigation hub data."""
        telemetry = self.get_live_telemetry()
        moisture = telemetry["soil_moisture"]["value"]

        # Update today's water usage if pump is running
        if self.pump_running:
            self.water_usage_7d[-1] += random.randint(2, 5)

        return {
            "status": "success",
            "optimal_window": {
                "message": f"Soil moisture at {moisture}%. " +
                           ("Run pump for 2 hours." if moisture < 50 else "No irrigation needed."),
                "should_water": moisture < 50,
            },
            "power_schedule": {"outage_start": "14:00", "outage_end": "16:00",
                               "note": "Plan irrigation around these hours."},
            "active_alerts": [
                {"title": f"Soil Moisture: {moisture}%",
                 "desc": f"Zone A moisture at {moisture}%.",
                 "severity": "danger" if moisture < 30 else "warning" if moisture < 50 else "info"},
                {"title": "Valve 3 Maintenance", "desc": "Scheduled check next week.",
                 "severity": "warning"},
            ],
            "water_usage_7d": self.water_usage_7d,
            "pump_running": self.pump_running,
        }

    def control_pump(self, action: str) -> dict:
        """Start or stop the pump."""
        if action == "start":
            self.pump_running = True
            self.pump_start_time = datetime.now()
            return {"status": "success", "pump": "running",
                    "message": "Pump started. Will auto-stop in 2 hours."}
        else:
            self.pump_running = False
            duration = ""
            if self.pump_start_time:
                mins = (datetime.now() - self.pump_start_time).seconds // 60
                duration = f" Ran for {mins} minutes."
            self.pump_start_time = None
            return {"status": "success", "pump": "stopped",
                    "message": f"Pump stopped.{duration}"}

    def sync(self) -> dict:
        """Force refresh sensor data."""
        # In production this would trigger MQTT refresh
        return {"status": "success", "message": "Sensor data refreshed",
                "timestamp": datetime.now().isoformat()}
