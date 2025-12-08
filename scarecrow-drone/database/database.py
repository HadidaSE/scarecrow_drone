#!/usr/bin/env python3
"""
SQLite Database for Scarecrow Drone
Stores flight data and telemetry records
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scarecrow.db")


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_database():
    """Initialize database with tables"""
    conn = get_connection()
    cursor = conn.cursor()

    # Flights table - one record per flight
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            status TEXT DEFAULT 'in_progress',
            notes TEXT
        )
    ''')

    # Telemetry table - one record per second during flight
    # Mode is always MANUAL (no GPS)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER NOT NULL,
            timestamp DATETIME NOT NULL,
            mode TEXT,
            armed INTEGER,
            location TEXT,
            attitude TEXT,
            groundspeed REAL,
            FOREIGN KEY (flight_id) REFERENCES flights (flight_id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


# =============================================================================
# Flight Operations
# =============================================================================

def start_flight(notes: str = None) -> int:
    """Start a new flight, returns flight_id"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO flights (start_time, status, notes)
        VALUES (?, 'in_progress', ?)
    ''', (datetime.now(), notes))

    flight_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return flight_id


def end_flight(flight_id: int, status: str = 'completed'):
    """End a flight"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE flights
        SET end_time = ?, status = ?
        WHERE flight_id = ?
    ''', (datetime.now(), status, flight_id))

    conn.commit()
    conn.close()


def get_flight(flight_id: int) -> Optional[Dict]:
    """Get flight by ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM flights WHERE flight_id = ?', (flight_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_all_flights() -> List[Dict]:
    """Get all flights"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM flights ORDER BY start_time DESC')
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# =============================================================================
# Telemetry Operations
# =============================================================================

def record_telemetry(flight_id: int, mode: str, armed: bool,
                     location: str, attitude: str, groundspeed: float):
    """Record one telemetry snapshot (called every second)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO telemetry (
            flight_id, timestamp, mode, armed, location, attitude, groundspeed
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        flight_id,
        datetime.now(),
        mode,
        1 if armed else 0,
        location,
        attitude,
        groundspeed
    ))

    conn.commit()
    conn.close()


def get_flight_telemetry(flight_id: int) -> List[Dict]:
    """Get all telemetry records for a flight"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM telemetry
        WHERE flight_id = ?
        ORDER BY timestamp ASC
    ''', (flight_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# =============================================================================
# Stats Operations
# =============================================================================

def get_flight_stats(flight_id: int) -> Optional[Dict]:
    """Get stats for a flight"""
    flight = get_flight(flight_id)
    if not flight:
        return None

    telemetry = get_flight_telemetry(flight_id)

    # Calculate duration
    duration = None
    if flight['end_time'] and flight['start_time']:
        start = datetime.fromisoformat(flight['start_time'])
        end = datetime.fromisoformat(flight['end_time'])
        duration = (end - start).total_seconds()

    return {
        'flight_id': flight_id,
        'start_time': flight['start_time'],
        'end_time': flight['end_time'],
        'duration_seconds': duration,
        'status': flight['status'],
        'telemetry_records': len(telemetry)
    }


# Initialize on import
if __name__ == "__main__":
    init_database()
    print("Database ready!")

    # Test: Create a sample flight
    print("\nTesting database operations...")

    # Start flight
    flight_id = start_flight(notes="Test flight")
    print(f"Started flight: {flight_id}")

    # Record telemetry (matches drone_info.py output)
    record_telemetry(
        flight_id=flight_id,
        mode="MANUAL",
        armed=True,
        location="LocationGlobalRelative:lat=32.0853,lon=34.7818,alt=1.0",
        attitude="Attitude:pitch=0.02,yaw=1.54,roll=-0.01",
        groundspeed=0.5
    )
    print("Recorded telemetry")

    # End flight
    end_flight(flight_id, status='completed')
    print("Ended flight")

    # Get stats
    stats = get_flight_stats(flight_id)
    print(f"\nFlight stats: {stats}")

    # Get telemetry
    telemetry = get_flight_telemetry(flight_id)
    print(f"\nTelemetry: {telemetry}")
