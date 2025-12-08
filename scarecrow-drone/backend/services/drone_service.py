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
        Returns: { isConnected, isFlying }
        """
        is_connected = self.drone_connection.is_connected()
        is_flying = self.drone_connection.is_flying()

        return {
            "isConnected": is_connected,
            "isFlying": is_flying
        }

    async def start_flight(self) -> dict:
        """
        Start a new flight - arms, takes off, hovers, and returns home
        Returns: { success, flightId }
        """
        # Check if SSH connected to drone
        if not self.connection_service.is_ssh_connected():
            return {
                "success": False,
                "flightId": None,
                "error": "Not connected to drone"
            }

        # Create flight record in database
        flight_id = self.drone_repository.start_flight()

        # Execute the flight script on the drone via SSH
        result = self.connection_service.start_flight()

        if result.get("success"):
            # Flight started successfully - stays in_progress until user stops/aborts
            return {
                "success": True,
                "flightId": str(flight_id),
                "output": result.get("output")
            }
        else:
            # Flight failed
            self.drone_repository.end_flight('failed')
            return {
                "success": False,
                "flightId": str(flight_id),
                "error": result.get("error", "Flight failed")
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

    async def abort_mission(self) -> dict:
        """
        Abort the current flight - emergency stop and land immediately
        Returns: { success }
        """
        flight_id = self.drone_repository.get_current_flight_id()

        # Command drone to abort
        result = self.connection_service.abort_mission()

        if result.get("success"):
            # End flight in database as aborted
            if flight_id is not None:
                self.drone_repository.end_flight('aborted')
            return {"success": True}
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to abort mission")
            }
