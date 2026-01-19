"""
Unit tests for DroneService.
Tests flight operations (start, stop, abort) with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestDroneService:
    """Test suite for DroneService class."""

    @pytest.fixture
    def mock_dependencies(self, mock_connection_service, mock_detection_service, mock_drone_repository):
        """Setup all mocked dependencies for DroneService."""
        return {
            'connection_service': mock_connection_service,
            'detection_service': mock_detection_service,
            'drone_repository': mock_drone_repository
        }

    @pytest.fixture
    def drone_service(self, mock_dependencies):
        """Create DroneService with mocked dependencies."""
        with patch('services.drone_service.ConnectionService', return_value=mock_dependencies['connection_service']), \
             patch('services.drone_service.DetectionService', return_value=mock_dependencies['detection_service']), \
             patch('services.drone_service.DroneRepository', return_value=mock_dependencies['drone_repository']), \
             patch('services.drone_service.DroneConnection'):

            from services.drone_service import DroneService
            service = DroneService()
            service.connection_service = mock_dependencies['connection_service']
            service.detection_service = mock_dependencies['detection_service']
            service.drone_repository = mock_dependencies['drone_repository']
            return service

    def test_get_status(self, drone_service):
        """Test getting drone status."""
        drone_service.drone_connection = Mock()
        drone_service.drone_connection.is_connected = Mock(return_value=True)
        drone_service.drone_connection.is_flying = Mock(return_value=False)

        status = drone_service.get_status()

        assert status["isConnected"] is True
        assert status["isFlying"] is False

    def test_get_status_flying(self, drone_service):
        """Test getting status when drone is flying."""
        drone_service.drone_connection = Mock()
        drone_service.drone_connection.is_connected = Mock(return_value=True)
        drone_service.drone_connection.is_flying = Mock(return_value=True)

        status = drone_service.get_status()

        assert status["isConnected"] is True
        assert status["isFlying"] is True

    @pytest.mark.asyncio
    async def test_start_flight_success(self, drone_service, mock_dependencies):
        """Test successful flight start."""
        mock_dependencies['drone_repository'].start_flight.return_value = 1
        mock_dependencies['connection_service'].start_video_stream.return_value = {"success": True}
        mock_dependencies['detection_service'].start_detection.return_value = {"success": True}

        result = await drone_service.start_flight()

        assert result["success"] is True
        assert result["flightId"] == "1"
        mock_dependencies['drone_repository'].start_flight.assert_called_once()
        mock_dependencies['detection_service'].start_detection.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_start_flight_video_stream_failure(self, drone_service, mock_dependencies):
        """Test flight start failure when video stream fails."""
        mock_dependencies['drone_repository'].start_flight.return_value = 1
        mock_dependencies['connection_service'].start_video_stream.return_value = {
            "success": False,
            "error": "Stream failed"
        }

        result = await drone_service.start_flight()

        assert result["success"] is False
        assert "Stream failed" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_start_flight_detection_failure(self, drone_service, mock_dependencies):
        """Test flight start failure when detection fails."""
        mock_dependencies['drone_repository'].start_flight.return_value = 1
        mock_dependencies['connection_service'].start_video_stream.return_value = {"success": True}
        mock_dependencies['detection_service'].start_detection.return_value = {
            "success": False,
            "error": "Detection failed"
        }

        result = await drone_service.start_flight()

        assert result["success"] is False
        assert "Detection failed" in result.get("error", "")
        # Video stream should be stopped
        mock_dependencies['connection_service'].stop_video_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_flight_success(self, drone_service, mock_dependencies):
        """Test successful flight stop."""
        mock_dependencies['drone_repository'].get_current_flight_id.return_value = 1
        mock_dependencies['detection_service'].stop_detection.return_value = {
            "detection_count": 5,
            "frames_processed": 100
        }
        mock_dependencies['connection_service'].stop_video_stream.return_value = {"success": True}

        result = await drone_service.stop_flight()

        assert result["success"] is True
        assert result["pigeonsDetected"] == 5
        assert result["framesProcessed"] == 100
        mock_dependencies['drone_repository'].end_flight.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_stop_flight_no_active_flight(self, drone_service, mock_dependencies):
        """Test stop flight when no flight is active."""
        mock_dependencies['drone_repository'].get_current_flight_id.return_value = None

        result = await drone_service.stop_flight()

        assert result["success"] is False
        assert "No active flight" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_abort_mission_success(self, drone_service, mock_dependencies):
        """Test successful mission abort."""
        mock_dependencies['drone_repository'].get_current_flight_id.return_value = 1
        mock_dependencies['detection_service'].stop_detection.return_value = {
            "detection_count": 3,
            "frames_processed": 50
        }
        mock_dependencies['connection_service'].stop_video_stream.return_value = {"success": True}

        result = await drone_service.abort_mission()

        assert result["success"] is True
        assert result["pigeonsDetected"] == 3
        assert result["framesProcessed"] == 50
        mock_dependencies['drone_repository'].end_flight.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_abort_mission_no_active_flight(self, drone_service, mock_dependencies):
        """Test abort when no flight is active - should still succeed."""
        mock_dependencies['drone_repository'].get_current_flight_id.return_value = None
        mock_dependencies['detection_service'].stop_detection.return_value = {
            "detection_count": 0,
            "frames_processed": 0
        }
        mock_dependencies['connection_service'].stop_video_stream.return_value = {"success": True}

        result = await drone_service.abort_mission()

        # Abort should still succeed even without active flight
        assert result["success"] is True
        # end_flight should NOT be called when there's no flight_id
        mock_dependencies['drone_repository'].end_flight.assert_not_called()
