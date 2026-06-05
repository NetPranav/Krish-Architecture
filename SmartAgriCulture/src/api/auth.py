"""
SQLite backed auth system for SmartAgri.
"""
import sqlite3
import os
import secrets
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'users.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                language TEXT,
                operation TEXT,
                farm_name TEXT,
                land_size REAL,
                land_unit TEXT,
                soil_type TEXT,
                location TEXT,
                lat REAL,
                lon REAL,
                voice_assistance BOOLEAN,
                membership TEXT,
                token TEXT UNIQUE
            )
        ''')
        conn.commit()

init_db()

def _get_user_by_token(token: str) -> Optional[dict]:
    if not token: return None
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
        if user:
            return dict(user)
    return None

def login(email_or_phone: str, password: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE phone = ? AND password = ?", (email_or_phone, password)).fetchone()
        if user:
            token = user['token']
            if not token:
                token = secrets.token_hex(16)
                conn.execute("UPDATE users SET token = ? WHERE id = ?", (token, user['id']))
                conn.commit()
            u_dict = dict(user)
            u_dict.pop('password', None)
            return {"status": "success", "token": token, "user": u_dict}
    return {"status": "error", "message": "Invalid credentials."}

def register(full_name: str, phone: str, password: str, language: str, operation: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        existing = conn.execute("SELECT id FROM users WHERE phone = ?", (phone,)).fetchone()
        if existing:
            return {"status": "error", "message": "Phone number already registered."}
        
        token = secrets.token_hex(16)
        conn.execute('''
            INSERT INTO users (full_name, phone, password, language, operation, token, farm_name, land_size, land_unit, soil_type, location, lat, lon, voice_assistance, membership)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, phone, password, language, operation, token, "My Farm", 5, "Acres", "Loamy", "Unknown Location", 20.0, 73.8, True, "Free"))
        conn.commit()
        
        user = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
        u_dict = dict(user)
        u_dict.pop('password', None)
        return {"status": "success", "message": "Account created successfully.", "token": token, "user": u_dict}

def get_profile(token: str) -> dict:
    user = _get_user_by_token(token)
    if user:
        user.pop('password', None)
        return user
    return {}

def update_profile(token: str, **kwargs) -> dict:
    user = _get_user_by_token(token)
    if not user:
        return {"status": "error", "message": "Unauthorized"}
    
    updates = []
    values = []
    allowed_keys = ['land_size', 'land_unit', 'soil_type', 'voice_assistance', 'language']
    for k, v in kwargs.items():
        if v is not None and k in allowed_keys:
            updates.append(f"{k} = ?")
            values.append(v)
            
    if updates:
        values.append(user['id'])
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            
    return {"status": "success", "profile": get_profile(token)}
