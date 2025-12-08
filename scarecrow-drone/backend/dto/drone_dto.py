from dataclasses import dataclass
from typing import Optional


@dataclass
class DroneStatusDTO:
    """DTO for drone status response - matches frontend DroneStatus interface"""
    is_connected: bool
    is_flying: bool

    def to_dict(self) -> dict:
        """Convert to camelCase dict for frontend"""
        return {
            "isConnected": self.is_connected,
            "isFlying": self.is_flying
        }


@dataclass
class StartFlightResponseDTO:
    """DTO for start flight response - matches frontend { success: boolean; flightId: string }"""
    success: bool
    flight_id: str

    def to_dict(self) -> dict:
        """Convert to camelCase dict for frontend"""
        return {
            "success": self.success,
            "flightId": self.flight_id
        }


@dataclass
class StopFlightResponseDTO:
    """DTO for stop flight response - matches frontend { success: boolean }"""
    success: bool

    def to_dict(self) -> dict:
        """Convert to camelCase dict for frontend"""
        return {
            "success": self.success
        }
