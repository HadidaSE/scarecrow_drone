from typing import List, Optional
from datetime import datetime
from database.db_connection import DatabaseConnection


class FlightRepository:
    """Repository for flight-related database operations"""

    def __init__(self):
        self.db = DatabaseConnection()

    def get_all_flights(self) -> List[dict]:
        """Get all flights from database ordered by start_time descending"""
        query = """
            SELECT flight_id, start_time, end_time, status, notes
            FROM flights
            ORDER BY start_time DESC
        """
        rows = self.db.execute_query(query)
        return [self._row_to_dict(row) for row in rows]

    def get_flight_by_id(self, flight_id: str) -> Optional[dict]:
        """Get a single flight by ID"""
        query = """
            SELECT flight_id, start_time, end_time, status, notes
            FROM flights
            WHERE flight_id = ?
        """
        rows = self.db.execute_query(query, (flight_id,))
        if rows:
            return self._row_to_dict(rows[0])
        return None

    def create_flight(self) -> int:
        """Create a new flight record and return the flight_id"""
        query = """
            INSERT INTO flights (start_time, status)
            VALUES (?, 'in_progress')
        """
        start_time = datetime.now().isoformat()
        flight_id = self.db.execute_write(query, (start_time,))
        return flight_id

    def end_flight(self, flight_id: int, status: str = 'completed') -> bool:
        """End a flight by setting end_time and status"""
        query = """
            UPDATE flights
            SET end_time = ?, status = ?
            WHERE flight_id = ?
        """
        end_time = datetime.now().isoformat()
        self.db.execute_write(query, (end_time, status, flight_id))
        return True

    def update_flight(self, flight_id: int, flight_data: dict) -> bool:
        """Update an existing flight record"""
        query = """
            UPDATE flights
            SET status = ?, notes = ?
            WHERE flight_id = ?
        """
        self.db.execute_write(query, (
            flight_data.get('status'),
            flight_data.get('notes'),
            flight_id
        ))
        return True

    def delete_flight(self, flight_id: int) -> bool:
        """Delete a flight record"""
        query = "DELETE FROM flights WHERE flight_id = ?"
        self.db.execute_write(query, (flight_id,))
        return True

    def _row_to_dict(self, row) -> dict:
        """Convert a database row to a dictionary"""
        start_time = row['start_time']
        end_time = row['end_time']

        # Calculate duration if both times exist
        duration = 0
        if start_time and end_time:
            try:
                start = datetime.fromisoformat(start_time)
                end = datetime.fromisoformat(end_time)
                duration = int((end - start).total_seconds())
            except:
                pass

        # Extract time portion
        start_time_only = ""
        end_time_only = ""
        if start_time:
            try:
                start_time_only = datetime.fromisoformat(start_time).strftime("%H:%M:%S")
            except:
                pass
        if end_time:
            try:
                end_time_only = datetime.fromisoformat(end_time).strftime("%H:%M:%S")
            except:
                pass

        return {
            "id": str(row['flight_id']),
            "date": start_time,
            "duration": duration,
            "pigeons_detected": 0,  # No pigeon detection data in telemetry table yet
            "status": row['status'],
            "start_time": start_time_only,
            "end_time": end_time_only
        }
