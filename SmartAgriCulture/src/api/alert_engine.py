"""
Alert generation engine — creates alerts from sensor thresholds,
weather conditions, and ML model predictions.
"""

from datetime import datetime, timedelta
import random


class AlertEngine:
    def __init__(self):
        self.alerts = []
        self._seed_alerts()

    def _seed_alerts(self):
        """Pre-populate with realistic alerts."""
        now = datetime.now()
        self.alerts = [
            {"id": "1", "title": "Severe Weather Warning", "time": now.strftime("%I:%M %p"),
             "desc": "Heavy rainfall and thunderstorms expected in your area within the next 2 hours.",
             "category": "Weather", "severity": "critical", "group": "TODAY",
             "route": "/weather", "read": False},
            {"id": "2", "title": "Pest Risk Elevated", "time": "08:15 AM",
             "desc": "Conditions favorable for Aphid infestation in Plot B (Tomatoes). Consider spraying.",
             "category": "Disease", "severity": "warning", "group": "TODAY",
             "route": "/scanner/capture", "read": False},
            {"id": "3", "title": "Price Surge — Onion", "time": "Yesterday, 4:30 PM",
             "desc": "Onion prices at Nashik Mandi increased by 15%. Current: ₹2,450/qtl.",
             "category": "Mandi", "severity": "info", "group": "YESTERDAY",
             "route": "/mandi", "read": False},
            {"id": "4", "title": "Low Soil Moisture", "time": "Yesterday, 9:00 AM",
             "desc": "Soil moisture in Plot A (Wheat) dropped below 30%. Irrigation recommended.",
             "category": "Irrigation", "severity": "warning", "group": "YESTERDAY",
             "route": "/alerts/irrigation", "read": False},
        ]

    def generate_from_sensors(self, sensors: dict) -> list:
        """Generate alerts from live sensor data."""
        new_alerts = []
        now = datetime.now()

        moisture = sensors.get("Moisture") or sensors.get("humidity", 60)
        if moisture and moisture < 30:
            new_alerts.append({
                "id": f"auto_{now.timestamp()}_moisture",
                "title": "Critical: Soil Moisture Low",
                "desc": f"Moisture at {moisture}%. Immediate irrigation needed.",
                "category": "Irrigation", "severity": "critical",
                "time": now.strftime("%I:%M %p"), "group": "TODAY",
                "route": "/alerts/irrigation", "read": False,
            })

        temp = sensors.get("temperature")
        if temp and temp > 40:
            new_alerts.append({
                "id": f"auto_{now.timestamp()}_heat",
                "title": "Heat Stress Warning",
                "desc": f"Temperature at {temp}°C. Crop damage risk is high.",
                "category": "Weather", "severity": "critical",
                "time": now.strftime("%I:%M %p"), "group": "TODAY",
                "route": "/weather", "read": False,
            })

        ph = sensors.get("ph")
        if ph and (ph < 5.5 or ph > 8.0):
            new_alerts.append({
                "id": f"auto_{now.timestamp()}_ph",
                "title": "Soil pH Out of Range",
                "desc": f"pH at {ph}. Optimal range is 6.0-7.5.",
                "category": "Irrigation", "severity": "warning",
                "time": now.strftime("%I:%M %p"), "group": "TODAY",
                "route": "/alerts/irrigation", "read": False,
            })

        return new_alerts

    def generate_from_weather(self, weather: dict) -> list:
        """Generate alerts from weather data."""
        new_alerts = []
        now = datetime.now()

        rain = weather.get("rain_probability", 0)
        if rain > 70:
            new_alerts.append({
                "id": f"auto_weather_{now.timestamp()}",
                "title": "Heavy Rain Expected",
                "desc": f"Rain probability {rain}%. Secure equipment and avoid spraying.",
                "category": "Weather", "severity": "critical" if rain > 85 else "warning",
                "time": now.strftime("%I:%M %p"), "group": "TODAY",
                "route": "/weather", "read": False,
            })

        temp = weather.get("temperature", 25)
        if temp < 5:
            new_alerts.append({
                "id": f"auto_frost_{now.timestamp()}",
                "title": "Frost Warning",
                "desc": f"Temperature dropping to {temp}°C. Cover sensitive crops.",
                "category": "Weather", "severity": "critical",
                "time": now.strftime("%I:%M %p"), "group": "TODAY",
                "route": "/weather", "read": False,
            })

        return new_alerts

    def generate_from_ml(self, fert_output: dict) -> list:
        """Generate alerts from fertilizer model predictions."""
        new_alerts = []
        now = datetime.now()

        water_idx = fert_output.get("Water_Requirement_Index", 0)
        if water_idx > 70:
            new_alerts.append({
                "id": f"auto_ml_water_{now.timestamp()}",
                "title": "AI: Irrigation Urgently Needed",
                "desc": f"Water Requirement Index at {water_idx:.0f}/100. Schedule irrigation today.",
                "category": "Irrigation", "severity": "critical",
                "time": now.strftime("%I:%M %p"), "group": "TODAY",
                "route": "/alerts/irrigation", "read": False,
            })

        fert_urgency = fert_output.get("Fertilizer_Urgency_Score", 0)
        if fert_urgency > 60:
            new_alerts.append({
                "id": f"auto_ml_fert_{now.timestamp()}",
                "title": "AI: Fertilizer Application Due",
                "desc": f"Urgency Score {fert_urgency:.0f}/100. Check nutrient report.",
                "category": "Disease", "severity": "warning",
                "time": now.strftime("%I:%M %p"), "group": "TODAY",
                "route": "/dashboard", "read": False,
            })

        return new_alerts

    def get_all(self) -> list:
        return self.alerts

    def mark_read(self, alert_id: str):
        for a in self.alerts:
            if a["id"] == alert_id:
                a["read"] = True

    def mark_all_read(self):
        for a in self.alerts:
            a["read"] = True
