from services.drone_connection import DroneConnection
from services.connection_service import ConnectionService
from services.detection_service import DetectionService
from database.drone_repository import DroneRepository


class DroneService:
    def __init__(self):
        self.drone_connection = DroneConnection()
        self.drone_repository = DroneRepository()
        self.connection_service = ConnectionService()
        self.detection_service = DetectionService()

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
        Also starts pigeon detection from video stream
        Returns: { success, flightId }
        """
        # Check if SSH connected to drone (commented out for testing detection only)
        # if not self.connection_service.is_ssh_connected():
        #     return {
        #         "success": False,
        #         "flightId": None,
        #         "error": "Not connected to drone"
        #     }

        # Create flight record in database
        flight_id = self.drone_repository.start_flight()

        # Start detection BEFORE flight (so it's ready when drone starts)
        detection_result = self.detection_service.start_detection(flight_id)
        if not detection_result.get("success"):
            print(f"[Warning] Detection failed to start: {detection_result.get('error')}")
            return {
                "success": False,
                "flightId": str(flight_id),
                "error": f"Detection failed: {detection_result.get('error')}"
            }

        # Execute the flight script on the drone via SSH (COMMENTED OUT FOR TESTING)
        # result = self.connection_service.start_flight()
        # Simulate successful flight for testing detection
        result = {"success": True, "output": "Detection only mode - no actual flight"}

        if result.get("success"):
            # Flight started successfully - stays in_progress until user stops/aborts
            return {
                "success": True,
                "flightId": str(flight_id),
                "output": result.get("output"),
                "detection": detection_result.get("success", False)
            }
        else:
            # Flight failed - stop detection if it was started
            if detection_result.get("success"):
                self.detection_service.stop_detection()
            
            self.drone_repository.end_flight('failed')
            return {
                "success": False,
                "flightId": str(flight_id),
                "error": result.get("error", "Flight failed")
            }

    async def stop_flight(self) -> dict:
        """
        Stop the current flight - commands drone to return home
        Stops detection and returns pigeon count
        Returns: { success, pigeonsDetected }
        """
        flight_id = self.drone_repository.get_current_flight_id()

        if flight_id is None:
            return {
                "success": False,
                "error": "No active flight"
            }

        # Stop detection and get count
        detection_result = self.detection_service.stop_detection()
        pigeon_count = detection_result.get("detection_count", 0)

        # Command drone to return to starting position (COMMENTED OUT FOR TESTING)
        # result = self.connection_service.return_home()
        # Simulate successful return for testing detection
        result = {"success": True}

        if result.get("success"):
            # End flight in database
            self.drone_repository.end_flight('completed')
            return {
                "success": True,
                "pigeonsDetected": pigeon_count
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to return home"),
                "pigeonsDetected": pigeon_count
            }

    async def abort_mission(self) -> dict:
        """
        Abort the current flight - emergency stop and land immediately
        Stops detection and returns pigeon count
        Returns: { success, pigeonsDetected }
        """
        flight_id = self.drone_repository.get_current_flight_id()

        # Stop detection
        detection_result = self.detection_service.stop_detection()
        pigeon_count = detection_result.get("detection_count", 0)

        # Command drone to abort (COMMENTED OUT FOR TESTING)
        # result = self.connection_service.abort_mission()
        # Simulate successful abort for testing detection
        result = {"success": True}

        if result.get("success"):
            # End flight in database as aborted
            if flight_id is not None:
                self.drone_repository.end_flight('aborted')
            return {
                "success": True,
                "pigeonsDetected": pigeon_count
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to abort mission"),
                "pigeonsDetected": pigeon_count
            }

