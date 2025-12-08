"""
Drone Connection Module
Handles WebSocket communication with drone scripts running on Intel Aero
"""
import json
from typing import Set
from fastapi import WebSocket


class DroneConnection:
    """Manages WebSocket connection with drone"""

    _instance = None

    # Connected WebSocket clients (drone + frontend listeners)
    _drone_websocket: WebSocket = None
    _frontend_websockets: Set[WebSocket] = set()

    # Current drone status
    _status = {
        "is_connected": False,
        "is_flying": False,
        "mode": "MANUAL",
        "armed": False,
        "location": {},
        "attitude": {},
        "groundspeed": 0.0
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    async def connect_drone(self, websocket: WebSocket) -> None:
        """Connect drone WebSocket"""
        await websocket.accept()
        DroneConnection._drone_websocket = websocket
        DroneConnection._status["is_connected"] = True
        await self._broadcast_to_frontends({"event": "drone_connected"})

    async def disconnect_drone(self) -> None:
        """Disconnect drone WebSocket"""
        DroneConnection._drone_websocket = None
        DroneConnection._status["is_connected"] = False
        DroneConnection._status["is_flying"] = False
        await self._broadcast_to_frontends({"event": "drone_disconnected"})

    async def connect_frontend(self, websocket: WebSocket) -> None:
        """Connect frontend WebSocket listener"""
        await websocket.accept()
        DroneConnection._frontend_websockets.add(websocket)
        # Send current status on connect
        await websocket.send_json(DroneConnection._status)

    def disconnect_frontend(self, websocket: WebSocket) -> None:
        """Disconnect frontend WebSocket listener"""
        DroneConnection._frontend_websockets.discard(websocket)

    async def receive_drone_data(self, data: dict) -> None:
        """Process incoming data from drone and broadcast to frontends"""
        DroneConnection._status.update(data)
        DroneConnection._status["is_connected"] = True
        await self._broadcast_to_frontends(DroneConnection._status)

    async def send_command_to_drone(self, command: dict) -> bool:
        """Send command to drone via WebSocket"""
        if DroneConnection._drone_websocket:
            await DroneConnection._drone_websocket.send_json(command)
            return True
        return False

    async def _broadcast_to_frontends(self, data: dict) -> None:
        """Broadcast data to all connected frontends"""
        disconnected = set()
        for websocket in DroneConnection._frontend_websockets:
            try:
                await websocket.send_json(data)
            except:
                disconnected.add(websocket)
        # Clean up disconnected clients
        DroneConnection._frontend_websockets -= disconnected

    def is_connected(self) -> bool:
        """Check if drone is connected"""
        return DroneConnection._status.get("is_connected", False)

    def is_flying(self) -> bool:
        """Check if drone is currently flying"""
        return DroneConnection._status.get("is_flying", False)

    def get_status(self) -> dict:
        """Get full drone status"""
        return DroneConnection._status.copy()

    def update_status_from_ssh(self, data: dict) -> None:
        """Update status from SSH subprocess (called by ConnectionService)"""
        DroneConnection._status["is_connected"] = data.get("is_connected", False)
        if "drone_id" in data:
            DroneConnection._status["drone_id"] = data["drone_id"]
