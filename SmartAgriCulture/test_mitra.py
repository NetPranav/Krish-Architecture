"""Quick test script for the Mitra API endpoint."""
import httpx
import json

URL = "http://localhost:8002/api/mitra/chat"

sensors = json.dumps({
    "N": 80, "P": 45, "K": 40,
    "temperature": 32, "humidity": 55,
    "ph": 6.3, "rainfall": 10
})

print("=" * 60)
print("  Testing Mitra API — POST /api/mitra/chat")
print("=" * 60)
print(f"  Sensors: {sensors}")
print()

response = httpx.post(
    URL,
    data={
        "text": "Should I water my rice field today? The leaves look a bit dry.",
        "sensors": sensors,
        "crop": "rice",
        "days": "45",
    },
    timeout=120.0,
)

print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
