"""
Unit tests for FastAPI Controllers.
Tests API endpoint logic with mocked services.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestConnectionController:
    """Test suite for connection_controller endpoints."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset singletons before each test."""
        from services.connection_service import ConnectionService
        ConnectionService._instance = None
        yield
        ConnectionService._instance = None

    @pytest.fixture
    def mock_connection_service(self):
        """Create mock connection service."""
        mock = Mock()
        mock.check_wifi_connection = Mock(return_value={"connected": True})
        mock.connect_ssh = AsyncMock(return_value={"success": True})
        mock.disconnect_ssh = Mock(return_value={"success": True})
        mock.get_connection_status = Mock(return_value={
            "wifiConnected": True,
            "sshConnected": True,
            "droneReady": True
        })
        return mock

    def test_check_wifi(self, mock_connection_service):
        """Test GET /api/connection/wifi endpoint."""
        with patch('controllers.connection_controller.connection_service', mock_connection_service):
            from controllers.connection_controller import check_wifi

            result = check_wifi()

            assert result["connected"] is True
            mock_connection_service.check_wifi_connection.assert_called_once()

    def test_check_wifi_disconnected(self, mock_connection_service):
        """Test GET /api/connection/wifi when disconnected."""
        mock_connection_service.check_wifi_connection.return_value = {"connected": False}

        with patch('controllers.connection_controller.connection_service', mock_connection_service):
            from controllers.connection_controller import check_wifi

            result = check_wifi()

            assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_connect_ssh_success(self, mock_connection_service):
        """Test POST /api/connection/ssh endpoint."""
        with patch('controllers.connection_controller.connection_service', mock_connection_service):
            from controllers.connection_controller import connect_ssh

            result = await connect_ssh()

            assert result["success"] is True
            mock_connection_service.connect_ssh.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_ssh_failure(self, mock_connection_service):
        """Test POST /api/connection/ssh when fails."""
        mock_connection_service.connect_ssh = AsyncMock(return_value={"success": False, "error": "Connection failed"})

        with patch('controllers.connection_controller.connection_service', mock_connection_service):
            from controllers.connection_controller import connect_ssh

            result = await connect_ssh()

            assert result["success"] is False

    def test_disconnect_ssh(self, mock_connection_service):
        """Test DELETE /api/connection/ssh endpoint."""
        with patch('controllers.connection_controller.connection_service', mock_connection_service):
            from controllers.connection_controller import disconnect_ssh

            result = disconnect_ssh()

            assert result["success"] is True
            mock_connection_service.disconnect_ssh.assert_called_once()

    def test_get_connection_status(self, mock_connection_service):
        """Test GET /api/connection/status endpoint."""
        with patch('controllers.connection_controller.connection_service', mock_connection_service):
            from controllers.connection_controller import get_connection_status

            result = get_connection_status()

            assert result["wifiConnected"] is True
            assert result["sshConnected"] is True
            assert result["droneReady"] is True


class TestDroneController:
    """Test suite for drone_controller endpoints."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset singletons before each test."""
        from services.drone_service import DroneService
        from services.connection_service import ConnectionService
        DroneService._instance = None
        ConnectionService._instance = None
        yield
        DroneService._instance = None
        ConnectionService._instance = None

    @pytest.fixture
    def mock_drone_service(self):
        """Create mock drone service."""
        mock = Mock()
        mock.get_status = Mock(return_value={
            "isConnected": True,
            "isFlying": False,
            "mode": "MANUAL"
        })
        mock.start_flight = AsyncMock(return_value={"success": True, "flightId": "1"})
        mock.stop_flight = AsyncMock(return_value={"success": True, "pigeonsDetected": 5})
        mock.abort_mission = AsyncMock(return_value={"success": True})
        return mock

    @pytest.fixture
    def mock_connection_service(self):
        """Create mock connection service."""
        mock = Mock()
        mock.return_home = Mock(return_value={"success": True})
        return mock

    def test_get_status(self, mock_drone_service):
        """Test GET /api/drone/status endpoint."""
        with patch('controllers.drone_controller.drone_service', mock_drone_service):
            from controllers.drone_controller import get_status

            result = get_status()

            assert result["isConnected"] is True
            assert result["isFlying"] is False
            mock_drone_service.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_flight(self, mock_drone_service):
        """Test POST /api/drone/start endpoint."""
        with patch('controllers.drone_controller.drone_service', mock_drone_service):
            from controllers.drone_controller import start_flight

            result = await start_flight()

            assert result["success"] is True
            assert result["flightId"] == "1"
            mock_drone_service.start_flight.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_flight_failure(self, mock_drone_service):
        """Test POST /api/drone/start when fails."""
        mock_drone_service.start_flight = AsyncMock(return_value={"success": False, "error": "Stream failed"})

        with patch('controllers.drone_controller.drone_service', mock_drone_service):
            from controllers.drone_controller import start_flight

            result = await start_flight()

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_stop_flight(self, mock_drone_service):
        """Test POST /api/drone/stop endpoint."""
        with patch('controllers.drone_controller.drone_service', mock_drone_service):
            from controllers.drone_controller import stop_flight

            result = await stop_flight()

            assert result["success"] is True
            assert result["pigeonsDetected"] == 5
            mock_drone_service.stop_flight.assert_called_once()

    def test_return_home(self, mock_connection_service):
        """Test POST /api/drone/return-home endpoint."""
        with patch('controllers.drone_controller.connection_service', mock_connection_service):
            from controllers.drone_controller import return_home

            result = return_home()

            assert result["success"] is True
            mock_connection_service.return_home.assert_called_once()

    @pytest.mark.asyncio
    async def test_abort_mission(self, mock_drone_service):
        """Test POST /api/drone/abort endpoint."""
        with patch('controllers.drone_controller.drone_service', mock_drone_service):
            from controllers.drone_controller import abort_mission

            result = await abort_mission()

            assert result["success"] is True
            mock_drone_service.abort_mission.assert_called_once()


class TestFlightController:
    """Test suite for flight_controller endpoints."""

    @pytest.fixture
    def mock_flight_service(self):
        """Create mock flight service."""
        mock = Mock()
        mock.get_flight_history = Mock(return_value=[
            {"id": "1", "date": "2025-01-19", "pigeonsDetected": 5},
            {"id": "2", "date": "2025-01-18", "pigeonsDetected": 3}
        ])
        mock.get_flight_summary = Mock(return_value={
            "flightId": "1",
            "duration": 120,
            "avgSpeed": 5.0
        })
        mock.get_detection_images = Mock(return_value=["/path/to/img1.jpg"])
        mock.get_flight_recording = Mock(return_value="/path/to/video.mp4")
        mock.get_flight = Mock(return_value={"id": "1", "pigeonsDetected": 5})
        return mock

    def test_get_flight_history(self, mock_flight_service):
        """Test GET /api/flights endpoint."""
        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_history

            result = get_flight_history()

            assert len(result) == 2
            assert result[0]["id"] == "1"
            mock_flight_service.get_flight_history.assert_called_once()

    def test_get_flight_history_empty(self, mock_flight_service):
        """Test GET /api/flights when no flights."""
        mock_flight_service.get_flight_history.return_value = []

        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_history

            result = get_flight_history()

            assert result == []

    def test_get_flight_summary(self, mock_flight_service):
        """Test GET /api/flights/:id/summary endpoint."""
        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_summary

            result = get_flight_summary("1")

            assert result["flightId"] == "1"
            assert result["duration"] == 120
            mock_flight_service.get_flight_summary.assert_called_once_with("1")

    def test_get_flight_summary_not_found(self, mock_flight_service):
        """Test GET /api/flights/:id/summary when not found."""
        mock_flight_service.get_flight_summary.return_value = None

        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_summary

            with pytest.raises(HTTPException) as exc_info:
                get_flight_summary("999")

            assert exc_info.value.status_code == 404

    def test_get_flight_images(self, mock_flight_service):
        """Test GET /api/flights/:id/images endpoint."""
        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_images

            result = get_flight_images("1")

            assert "images" in result
            assert len(result["images"]) == 1
            mock_flight_service.get_detection_images.assert_called_once_with("1")

    def test_get_flight_images_empty(self, mock_flight_service):
        """Test GET /api/flights/:id/images when no images."""
        mock_flight_service.get_detection_images.return_value = []

        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_images

            result = get_flight_images("1")

            assert result["images"] == []

    def test_get_flight_recording(self, mock_flight_service):
        """Test GET /api/flights/:id/recording endpoint."""
        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_recording

            result = get_flight_recording("1")

            assert "recording" in result
            assert result["recording"] == "/path/to/video.mp4"
            mock_flight_service.get_flight_recording.assert_called_once_with("1")

    def test_get_flight_recording_none(self, mock_flight_service):
        """Test GET /api/flights/:id/recording when no recording."""
        mock_flight_service.get_flight_recording.return_value = None

        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight_recording

            result = get_flight_recording("1")

            assert result["recording"] is None

    def test_get_flight(self, mock_flight_service):
        """Test GET /api/flights/:id endpoint."""
        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight

            result = get_flight("1")

            assert result["id"] == "1"
            assert result["pigeonsDetected"] == 5
            mock_flight_service.get_flight.assert_called_once_with("1")

    def test_get_flight_not_found(self, mock_flight_service):
        """Test GET /api/flights/:id when not found."""
        mock_flight_service.get_flight.return_value = None

        with patch('controllers.flight_controller.flight_service', mock_flight_service):
            from controllers.flight_controller import get_flight

            with pytest.raises(HTTPException) as exc_info:
                get_flight("999")

            assert exc_info.value.status_code == 404
            assert "Flight not found" in str(exc_info.value.detail)
