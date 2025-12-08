from typing import List, Optional
import json
from dto.flight_dto import FlightDTO
from database.flight_repository import FlightRepository
from database.drone_repository import DroneRepository


class FlightService:
    def __init__(self):
        self.flight_repository = FlightRepository()
        self.drone_repository = DroneRepository()

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

    def get_flight_summary(self, flight_id: str) -> Optional[dict]:
        """
        Get flight summary with stats calculated from telemetry
        Returns: { flightId, droneId, duration, avgSpeed, avgAltitude, status }
        """
        flight = self.flight_repository.get_flight_by_id(flight_id)
        if not flight:
            return None

        telemetry = self.drone_repository.get_flight_telemetry(int(flight_id))

        # Calculate averages from telemetry
        avg_speed = 0.0
        avg_altitude = 0.0

        if telemetry:
            speeds = []
            altitudes = []
            for t in telemetry:
                speeds.append(t.get("groundspeed", 0) or 0)
                location = t.get("location", "{}")
                if isinstance(location, str):
                    try:
                        location = json.loads(location)
                    except:
                        location = {}
                altitudes.append(location.get("alt", 0) or 0)

            if speeds:
                avg_speed = sum(speeds) / len(speeds)
            if altitudes:
                avg_altitude = sum(altitudes) / len(altitudes)

        return {
            "flightId": flight.get("id"),
            "droneId": 1,  # Currently single drone
            "duration": flight.get("duration", 0),
            "avgSpeed": round(avg_speed, 2),
            "avgAltitude": round(avg_altitude, 2),
            "status": flight.get("status"),
            "date": flight.get("date"),
            "startTime": flight.get("start_time"),
            "endTime": flight.get("end_time")
        }

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

    def _format_telemetry(self, telemetry: dict) -> dict:
        """Format telemetry data for frontend"""
        # Parse JSON fields
        location = telemetry.get("location", "{}")
        attitude = telemetry.get("attitude", "{}")

        if isinstance(location, str):
            try:
                location = json.loads(location)
            except:
                location = {}
        if isinstance(attitude, str):
            try:
                attitude = json.loads(attitude)
            except:
                attitude = {}

        return {
            "id": telemetry.get("id"),
            "timestamp": telemetry.get("timestamp"),
            "mode": telemetry.get("mode"),
            "armed": bool(telemetry.get("armed")),
            "altitude": location.get("alt", 0),
            "latitude": location.get("lat", 0),
            "longitude": location.get("lon", 0),
            "pitch": attitude.get("pitch", 0),
            "roll": attitude.get("roll", 0),
            "yaw": attitude.get("yaw", 0),
            "groundspeed": telemetry.get("groundspeed", 0)
        }
