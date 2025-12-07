from database.db_connection import DatabaseConnection
from database.flight_repository import FlightRepository


class DroneRepository:
    """Repository for drone-related database operations"""

    # Track current flight in memory (not persisted)
    _current_flight_id = None

    def __init__(self):
        self.db = DatabaseConnection()
        self.flight_repository = FlightRepository()

    def get_current_flight_id(self) -> int:
        """Get current in-progress flight ID"""
        return DroneRepository._current_flight_id

    def start_flight(self) -> int:
        """Create a new flight record and return the flight_id"""
        flight_id = self.flight_repository.create_flight()
        DroneRepository._current_flight_id = flight_id
        return flight_id

    def end_flight(self, status: str = 'completed') -> bool:
        """End the current flight"""
        if DroneRepository._current_flight_id is None:
            return False

        self.flight_repository.end_flight(DroneRepository._current_flight_id, status)
        DroneRepository._current_flight_id = None
        return True

    def save_telemetry(self, flight_id: int, telemetry_data: dict) -> bool:
        """Save telemetry data for a flight"""
        query = """
            INSERT INTO telemetry
            (flight_id, timestamp, mode, armed, battery, gps, location, attitude, groundspeed)
            VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)
        """
        import json
        self.db.execute_write(query, (
            flight_id,
            telemetry_data.get('mode'),
            1 if telemetry_data.get('armed') else 0,
            json.dumps(telemetry_data.get('battery', {})),
            json.dumps(telemetry_data.get('gps', {})),
            json.dumps(telemetry_data.get('location', {})),
            json.dumps(telemetry_data.get('attitude', {})),
            telemetry_data.get('groundspeed', 0)
        ))
        return True

    def get_flight_telemetry(self, flight_id: int) -> list:
        """Get all telemetry data for a flight"""
        query = """
            SELECT * FROM telemetry
            WHERE flight_id = ?
            ORDER BY timestamp ASC
        """
        rows = self.db.execute_query(query, (flight_id,))
        return [dict(row) for row in rows]
