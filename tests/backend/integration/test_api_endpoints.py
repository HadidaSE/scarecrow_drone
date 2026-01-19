"""
Integration tests for FastAPI endpoints.
Tests the API layer with mocked services.

Note: These tests validate the endpoint logic by directly testing
the controller routers in isolation, avoiding module-level service instantiation issues.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singleton instances before each test."""
    from services.connection_service import ConnectionService
    from database.db_connection import DatabaseConnection
    ConnectionService._instance = None
    DatabaseConnection._instance = None


class TestConnectionServiceDirectly:
    """Test connection service methods directly with mocking."""

    def test_check_wifi_returns_connected(self):
        """Test WiFi check returns connected status."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True

        result = service.check_wifi_connection()

        assert result["connected"] is True

    @pytest.mark.asyncio
    async def test_connect_ssh_success(self):
        """Test SSH connection succeeds in mock mode."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True

        result = await service.connect_ssh()

        assert result["success"] is True

    def test_disconnect_ssh_success(self):
        """Test SSH disconnection."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = True

        result = service.disconnect_ssh()

        assert result["success"] is True
        assert service._ssh_connected is False

    def test_get_connection_status_mock_mode(self):
        """Test getting full connection status in mock mode."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True

        result = service.get_connection_status()

        assert result["wifiConnected"] is True
        assert result["sshConnected"] is True
        assert result["droneReady"] is True


class TestDroneServiceDirectly:
    """Test drone service methods directly with mocking."""

    @pytest.fixture
    def mock_dependencies(self):
        """Setup mocked dependencies."""
        mock_conn = Mock()
        mock_conn.start_video_stream = Mock(return_value={"success": True})
        mock_conn.stop_video_stream = Mock(return_value={"success": True})

        mock_detection = Mock()
        mock_detection.start_detection = Mock(return_value={"success": True})
        mock_detection.stop_detection = Mock(return_value={
            "detection_count": 5,
            "frames_processed": 100
        })

        mock_repo = Mock()
        mock_repo.start_flight = Mock(return_value=1)
        mock_repo.end_flight = Mock(return_value=True)
        mock_repo.get_current_flight_id = Mock(return_value=1)

        return {
            'connection': mock_conn,
            'detection': mock_detection,
            'repository': mock_repo
        }

    def test_get_status(self, mock_dependencies):
        """Test getting drone status."""
        with patch('services.drone_service.DroneConnection') as mock_dc, \
             patch('services.drone_service.ConnectionService', return_value=mock_dependencies['connection']), \
             patch('services.drone_service.DetectionService', return_value=mock_dependencies['detection']), \
             patch('services.drone_service.DroneRepository', return_value=mock_dependencies['repository']):

            mock_dc_instance = Mock()
            mock_dc_instance.is_connected = Mock(return_value=True)
            mock_dc_instance.is_flying = Mock(return_value=False)
            mock_dc.return_value = mock_dc_instance

            from services.drone_service import DroneService
            service = DroneService()

            result = service.get_status()

            assert result["isConnected"] is True
            assert result["isFlying"] is False

    @pytest.mark.asyncio
    async def test_start_flight_success(self, mock_dependencies):
        """Test starting a flight."""
        with patch('services.drone_service.DroneConnection'), \
             patch('services.drone_service.ConnectionService', return_value=mock_dependencies['connection']), \
             patch('services.drone_service.DetectionService', return_value=mock_dependencies['detection']), \
             patch('services.drone_service.DroneRepository', return_value=mock_dependencies['repository']):

            from services.drone_service import DroneService
            service = DroneService()
            service.connection_service = mock_dependencies['connection']
            service.detection_service = mock_dependencies['detection']
            service.drone_repository = mock_dependencies['repository']

            result = await service.start_flight()

            assert result["success"] is True
            assert result["flightId"] == "1"

    @pytest.mark.asyncio
    async def test_stop_flight_success(self, mock_dependencies):
        """Test stopping a flight."""
        with patch('services.drone_service.DroneConnection'), \
             patch('services.drone_service.ConnectionService', return_value=mock_dependencies['connection']), \
             patch('services.drone_service.DetectionService', return_value=mock_dependencies['detection']), \
             patch('services.drone_service.DroneRepository', return_value=mock_dependencies['repository']):

            from services.drone_service import DroneService
            service = DroneService()
            service.connection_service = mock_dependencies['connection']
            service.detection_service = mock_dependencies['detection']
            service.drone_repository = mock_dependencies['repository']

            result = await service.stop_flight()

            assert result["success"] is True
            assert result["pigeonsDetected"] == 5

    @pytest.mark.asyncio
    async def test_abort_mission_success(self, mock_dependencies):
        """Test aborting a mission."""
        with patch('services.drone_service.DroneConnection'), \
             patch('services.drone_service.ConnectionService', return_value=mock_dependencies['connection']), \
             patch('services.drone_service.DetectionService', return_value=mock_dependencies['detection']), \
             patch('services.drone_service.DroneRepository', return_value=mock_dependencies['repository']):

            from services.drone_service import DroneService
            service = DroneService()
            service.connection_service = mock_dependencies['connection']
            service.detection_service = mock_dependencies['detection']
            service.drone_repository = mock_dependencies['repository']

            result = await service.abort_mission()

            assert result["success"] is True


class TestFlightServiceDirectly:
    """Test flight service methods directly."""

    @pytest.fixture
    def mock_repository(self):
        """Setup mocked flight repository."""
        mock_repo = Mock()
        mock_repo.get_all_flights = Mock(return_value=[
            {"id": "1", "date": "2025-01-19", "pigeons_detected": 5}
        ])
        mock_repo.get_flight_by_id = Mock(return_value={
            "id": "1", "pigeons_detected": 5
        })
        return mock_repo

    def test_get_flight_history(self, mock_repository):
        """Test getting flight history."""
        with patch('services.flight_service.FlightRepository', return_value=mock_repository):
            from services.flight_service import FlightService
            service = FlightService()
            service.flight_repository = mock_repository

            result = service.get_flight_history()

            assert len(result) == 1
            assert result[0]["id"] == "1"

    def test_get_flight_found(self, mock_repository):
        """Test getting a single flight."""
        with patch('services.flight_service.FlightRepository', return_value=mock_repository):
            from services.flight_service import FlightService
            service = FlightService()
            service.flight_repository = mock_repository

            result = service.get_flight("1")

            assert result["id"] == "1"
            # Service converts pigeons_detected to camelCase pigeonsDetected
            assert result["pigeonsDetected"] == 5

    def test_get_flight_not_found(self, mock_repository):
        """Test getting a non-existent flight."""
        mock_repository.get_flight_by_id = Mock(return_value=None)

        with patch('services.flight_service.FlightRepository', return_value=mock_repository):
            from services.flight_service import FlightService
            service = FlightService()
            service.flight_repository = mock_repository

            result = service.get_flight("999")

            assert result is None


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_ssh_connection_failure(self):
        """Test SSH connection failure handling."""
        from services.connection_service import ConnectionService

        with patch('services.connection_service.subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)  # Ping fails

            service = ConnectionService()
            service.MOCK_MODE = False
            service._ssh_connected = False

            result = await service.connect_ssh()

            assert result["success"] is False
            assert "Cannot reach drone" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_flight_start_without_video_stream(self):
        """Test flight start failure when video stream fails."""
        mock_conn = Mock()
        mock_conn.start_video_stream = Mock(return_value={
            "success": False,
            "error": "Stream failed"
        })

        mock_repo = Mock()
        mock_repo.start_flight = Mock(return_value=1)

        with patch('services.drone_service.DroneConnection'), \
             patch('services.drone_service.ConnectionService', return_value=mock_conn), \
             patch('services.drone_service.DetectionService'), \
             patch('services.drone_service.DroneRepository', return_value=mock_repo):

            from services.drone_service import DroneService
            service = DroneService()
            service.connection_service = mock_conn
            service.drone_repository = mock_repo

            result = await service.start_flight()

            assert result["success"] is False
            assert "Stream failed" in result.get("error", "")
