"""
Hardcoded single-user auth system.
Login: phone=9876543210, password=smartagri123
"""

HARDCODED_USER = {
    "id": 1,
    "full_name": "Ramesh Kumar",
    "phone": "9876543210",
    "email": "ramesh@smartagri.in",
    "password": "smartagri123",
    "language": "en",
    "operation": "crop",
    "farm_name": "Sunrise Farms",
    "land_size": 15,
    "land_unit": "Acres",
    "soil_type": "Loamy",
    "location": "Nashik, Maharashtra",
    "lat": 20.0063,
    "lon": 73.7895,
    "voice_assistance": True,
    "membership": "Premium",
}

# Simple token (no JWT library needed)
VALID_TOKEN = "smartagri-session-token-ramesh-001"


def login(email_or_phone: str, password: str) -> dict:
    u = HARDCODED_USER
    if (email_or_phone in (u["phone"], u["email"])) and password == u["password"]:
        return {"status": "success", "token": VALID_TOKEN,
                "user": {k: v for k, v in u.items() if k != "password"}}
    return {"status": "error", "message": "Invalid credentials. Use phone: 9876543210, password: smartagri123"}


def register(full_name: str, phone: str, language: str, operation: str) -> dict:
    return {"status": "success", "message": "Account created (demo mode — single hardcoded user)",
            "token": VALID_TOKEN,
            "user": {**HARDCODED_USER, "full_name": full_name, "phone": phone,
                     "language": language, "operation": operation}}


def get_profile() -> dict:
    return {k: v for k, v in HARDCODED_USER.items() if k != "password"}


def update_profile(**kwargs) -> dict:
    for k, v in kwargs.items():
        if v is not None and k in HARDCODED_USER:
            HARDCODED_USER[k] = v
    return {"status": "success", "profile": get_profile()}
