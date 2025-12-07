from typing import List, Optional
from dto.flight_dto import FlightDTO
from database.flight_repository import FlightRepository


class FlightService:
    def __init__(self):
        self.flight_repository = FlightRepository()

    def get_flight_history(self) -> List[dict]:
        """
        Get all flight history
        Returns: Array of { id, date, duration, pigeonsDetected, status, startTime, endTime }
        """
        flights = self.flight_repository.get_all_flights()
        return [self._format_flight(flight) for flight in flights]

    def get_flight(self, flight_id: str) -> Optional[dict]:
        """
        Get a single flight by ID
        Returns: { id, date, duration, pigeonsDetected, status, startTime, endTime }
        """
        flight = self.flight_repository.get_flight_by_id(flight_id)
        if flight:
            return self._format_flight(flight)
        return None

    def _format_flight(self, flight: dict) -> dict:
        """Format flight data to camelCase for frontend"""
        return {
            "id": flight.get("id"),
            "date": flight.get("date"),
            "duration": flight.get("duration"),
            "pigeonsDetected": flight.get("pigeons_detected", 0),
            "status": flight.get("status"),
            "startTime": flight.get("start_time"),
            "endTime": flight.get("end_time")
        }
