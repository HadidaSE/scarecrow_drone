from dataclasses import dataclass
from typing import Optional


@dataclass
class FlightDTO:
    """DTO for flight data - matches frontend Flight interface"""
    id: str
    date: str
    duration: int
    pigeons_detected: int
    status: str  # 'completed' | 'in_progress' | 'failed'
    start_time: str
    end_time: Optional[str]

    def to_dict(self) -> dict:
        """Convert to camelCase dict for frontend"""
        return {
            "id": self.id,
            "date": self.date,
            "duration": self.duration,
            "pigeonsDetected": self.pigeons_detected,
            "status": self.status,
            "startTime": self.start_time,
            "endTime": self.end_time
        }

    @staticmethod
    def from_db_row(row: dict) -> 'FlightDTO':
        """Create FlightDTO from database row"""
        return FlightDTO(
            id=str(row.get("id", "")),
            date=row.get("date", ""),
            duration=row.get("duration", 0),
            pigeons_detected=row.get("pigeons_detected", 0),
            status=row.get("status", ""),
            start_time=row.get("start_time", ""),
            end_time=row.get("end_time")
        )
