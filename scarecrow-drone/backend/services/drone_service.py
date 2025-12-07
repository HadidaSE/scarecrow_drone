from services.drone_connection import DroneConnection
from services.connection_service import ConnectionService
from database.drone_repository import DroneRepository


class DroneService:
    def __init__(self):
        self.drone_connection = DroneConnection()
        self.drone_repository = DroneRepository()
        self.connection_service = ConnectionService()

    def get_status(self) -> dict:
        """
        Get current drone status from live drone connection
        Returns: { isConnected, isFlying, batteryLevel }
        """
        is_connected = self.drone_connection.is_connected()
        is_flying = self.drone_connection.is_flying()
        battery_level = self.drone_connection.get_battery_level()

        return {
            "isConnected": is_connected,
            "isFlying": is_flying,
            "batteryLevel": battery_level
        }

    async def start_flight(self) -> dict:
        """
        Start a new flight
        Returns: { success, flightId }
        """
        # Check if drone is connected
        if not self.drone_connection.is_connected():
            return {
                "success": False,
                "flightId": None,
                "error": "Drone not connected"
            }

        # Create flight record in database
        flight_id = self.drone_repository.start_flight()

        # Send start command to drone via WebSocket
        command_sent = await self.drone_connection.send_command_to_drone({
            "command": "start_flight",
            "flight_id": flight_id
        })

        return {
            "success": command_sent,
            "flightId": str(flight_id)
        }

    async def stop_flight(self) -> dict:
        """
        Stop the current flight - commands drone to return home
        Returns: { success }
        """
        flight_id = self.drone_repository.get_current_flight_id()

        if flight_id is None:
            return {
                "success": False,
                "error": "No active flight"
            }

        # Command drone to return to starting position
        result = self.connection_service.return_home()

        if result.get("success"):
            # End flight in database
            self.drone_repository.end_flight('completed')
            return {"success": True}
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to return home")
            }
