"""
Unit tests for FlightService.
Tests flight data retrieval and formatting.
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestFlightService:
    """Test suite for FlightService class."""

    @pytest.fixture
    def mock_flight_repo(self):
        """Create mock flight repository."""
        mock = Mock()
        mock.get_all_flights = Mock(return_value=[])
        mock.get_flight_by_id = Mock(return_value=None)
        return mock

    @pytest.fixture
    def mock_drone_repo(self):
        """Create mock drone repository."""
        mock = Mock()
        mock.get_detection_images = Mock(return_value=[])
        mock.get_video_recordings = Mock(return_value=[])
        mock.get_flight_telemetry = Mock(return_value=[])
        return mock

    @pytest.fixture
    def flight_service(self, mock_flight_repo, mock_drone_repo):
        """Create FlightService with mocked dependencies."""
        with patch('services.flight_service.FlightRepository', return_value=mock_flight_repo), \
             patch('services.flight_service.DroneRepository', return_value=mock_drone_repo):
            from services.flight_service import FlightService
            service = FlightService()
            service.flight_repository = mock_flight_repo
            service.drone_repository = mock_drone_repo
            return service

    def test_get_flight_history_empty(self, flight_service, mock_flight_repo):
        """Test get_flight_history with no flights."""
        mock_flight_repo.get_all_flights.return_value = []

        result = flight_service.get_flight_history()

        assert result == []
        mock_flight_repo.get_all_flights.assert_called_once()

    def test_get_flight_history_with_flights(self, flight_service, mock_flight_repo):
        """Test get_flight_history with multiple flights."""
        mock_flight_repo.get_all_flights.return_value = [
            {"id": "1", "date": "2025-01-19", "duration": 120, "pigeons_detected": 5, "status": "completed", "start_time": "10:00:00", "end_time": "10:02:00"},
            {"id": "2", "date": "2025-01-18", "duration": 90, "pigeons_detected": 3, "status": "completed", "start_time": "09:00:00", "end_time": "09:01:30"}
        ]

        result = flight_service.get_flight_history()

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[0]["pigeonsDetected"] == 5
        assert result[1]["id"] == "2"
        assert result[1]["pigeonsDetected"] == 3

    def test_get_flight_found(self, flight_service, mock_flight_repo):
        """Test get_flight when flight exists."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1", "date": "2025-01-19", "duration": 120,
            "pigeons_detected": 5, "status": "completed",
            "start_time": "10:00:00", "end_time": "10:02:00"
        }

        result = flight_service.get_flight("1")

        assert result["id"] == "1"
        assert result["pigeonsDetected"] == 5
        assert result["startTime"] == "10:00:00"
        assert result["endTime"] == "10:02:00"

    def test_get_flight_not_found(self, flight_service, mock_flight_repo):
        """Test get_flight when flight doesn't exist."""
        mock_flight_repo.get_flight_by_id.return_value = None

        result = flight_service.get_flight("999")

        assert result is None

    def test_get_detection_images(self, flight_service, mock_drone_repo):
        """Test get_detection_images returns image paths."""
        mock_drone_repo.get_detection_images.return_value = [
            "/path/to/image1.jpg",
            "/path/to/image2.jpg"
        ]

        result = flight_service.get_detection_images("1")

        assert len(result) == 2
        assert "/path/to/image1.jpg" in result
        mock_drone_repo.get_detection_images.assert_called_once_with(1)

    def test_get_video_recordings(self, flight_service, mock_drone_repo):
        """Test get_video_recordings returns video paths."""
        mock_drone_repo.get_video_recordings.return_value = [
            "/path/to/video1.mp4"
        ]

        result = flight_service.get_video_recordings("1")

        assert len(result) == 1
        assert "/path/to/video1.mp4" in result
        mock_drone_repo.get_video_recordings.assert_called_once_with(1)

    def test_get_flight_recording_found(self, flight_service, mock_flight_repo):
        """Test get_flight_recording when recording exists."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1",
            "video_path": "/path/to/recording.mp4"
        }

        result = flight_service.get_flight_recording("1")

        assert result == "/path/to/recording.mp4"

    def test_get_flight_recording_not_found(self, flight_service, mock_flight_repo):
        """Test get_flight_recording when no flight."""
        mock_flight_repo.get_flight_by_id.return_value = None

        result = flight_service.get_flight_recording("999")

        assert result is None

    def test_get_flight_recording_no_video(self, flight_service, mock_flight_repo):
        """Test get_flight_recording when flight has no video."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1"
        }

        result = flight_service.get_flight_recording("1")

        assert result is None

    def test_get_flight_summary_not_found(self, flight_service, mock_flight_repo):
        """Test get_flight_summary when flight doesn't exist."""
        mock_flight_repo.get_flight_by_id.return_value = None

        result = flight_service.get_flight_summary("999")

        assert result is None

    def test_get_flight_summary_no_telemetry(self, flight_service, mock_flight_repo, mock_drone_repo):
        """Test get_flight_summary with no telemetry data."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1", "date": "2025-01-19", "duration": 120,
            "status": "completed", "start_time": "10:00:00", "end_time": "10:02:00"
        }
        mock_drone_repo.get_flight_telemetry.return_value = []

        result = flight_service.get_flight_summary("1")

        assert result["flightId"] == "1"
        assert result["avgSpeed"] == 0.0
        assert result["avgAltitude"] == 0.0
        assert result["duration"] == 120

    def test_get_flight_summary_with_telemetry(self, flight_service, mock_flight_repo, mock_drone_repo):
        """Test get_flight_summary with telemetry data."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1", "date": "2025-01-19", "duration": 120,
            "status": "completed", "start_time": "10:00:00", "end_time": "10:02:00"
        }
        mock_drone_repo.get_flight_telemetry.return_value = [
            {"groundspeed": 5.0, "location": '{"lat": 32.0, "lon": 34.0, "alt": 10.0}'},
            {"groundspeed": 7.0, "location": '{"lat": 32.1, "lon": 34.1, "alt": 20.0}'},
            {"groundspeed": 6.0, "location": '{"lat": 32.2, "lon": 34.2, "alt": 15.0}'}
        ]

        result = flight_service.get_flight_summary("1")

        assert result["flightId"] == "1"
        assert result["avgSpeed"] == 6.0  # (5+7+6)/3
        assert result["avgAltitude"] == 15.0  # (10+20+15)/3
        assert result["droneId"] == 1

    def test_get_flight_summary_with_dict_location(self, flight_service, mock_flight_repo, mock_drone_repo):
        """Test get_flight_summary when location is already a dict."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1", "duration": 60, "status": "completed"
        }
        mock_drone_repo.get_flight_telemetry.return_value = [
            {"groundspeed": 5.0, "location": {"lat": 32.0, "lon": 34.0, "alt": 10.0}}
        ]

        result = flight_service.get_flight_summary("1")

        assert result["avgAltitude"] == 10.0

    def test_get_flight_summary_with_invalid_json_location(self, flight_service, mock_flight_repo, mock_drone_repo):
        """Test get_flight_summary with invalid JSON location."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1", "duration": 60, "status": "completed"
        }
        mock_drone_repo.get_flight_telemetry.return_value = [
            {"groundspeed": 5.0, "location": "invalid json"}
        ]

        result = flight_service.get_flight_summary("1")

        # Should handle gracefully and return 0 for altitude
        assert result["avgAltitude"] == 0.0

    def test_get_flight_summary_with_none_values(self, flight_service, mock_flight_repo, mock_drone_repo):
        """Test get_flight_summary with None values in telemetry."""
        mock_flight_repo.get_flight_by_id.return_value = {
            "id": "1", "duration": 60, "status": "completed"
        }
        mock_drone_repo.get_flight_telemetry.return_value = [
            {"groundspeed": None, "location": '{"alt": null}'},
            {"groundspeed": 5.0, "location": '{"alt": 10.0}'}
        ]

        result = flight_service.get_flight_summary("1")

        # Should handle None gracefully
        assert result["avgSpeed"] == 2.5  # (0+5)/2
        assert result["avgAltitude"] == 5.0  # (0+10)/2

    def test_format_flight_converts_keys(self, flight_service):
        """Test _format_flight converts snake_case to camelCase."""
        flight_data = {
            "id": "1",
            "date": "2025-01-19",
            "duration": 120,
            "pigeons_detected": 5,
            "status": "completed",
            "start_time": "10:00:00",
            "end_time": "10:02:00"
        }

        result = flight_service._format_flight(flight_data)

        assert "pigeonsDetected" in result
        assert "pigeons_detected" not in result
        assert "startTime" in result
        assert "start_time" not in result
        assert "endTime" in result
        assert "end_time" not in result

    def test_format_flight_handles_missing_keys(self, flight_service):
        """Test _format_flight handles missing optional keys."""
        flight_data = {"id": "1"}

        result = flight_service._format_flight(flight_data)

        assert result["id"] == "1"
        assert result["pigeonsDetected"] == 0  # Default value
        assert result["date"] is None

    def test_format_telemetry(self, flight_service):
        """Test _format_telemetry converts telemetry data."""
        telemetry = {
            "id": 1,
            "timestamp": "2025-01-19T10:00:00",
            "mode": "GUIDED",
            "armed": 1,
            "location": '{"lat": 32.0, "lon": 34.0, "alt": 10.0}',
            "attitude": '{"pitch": 0.1, "roll": 0.2, "yaw": 0.3}',
            "groundspeed": 5.0
        }

        result = flight_service._format_telemetry(telemetry)

        assert result["id"] == 1
        assert result["mode"] == "GUIDED"
        assert result["armed"] is True
        assert result["altitude"] == 10.0
        assert result["latitude"] == 32.0
        assert result["longitude"] == 34.0
        assert result["pitch"] == 0.1
        assert result["roll"] == 0.2
        assert result["yaw"] == 0.3

    def test_format_telemetry_with_dict_values(self, flight_service):
        """Test _format_telemetry when location/attitude are already dicts."""
        telemetry = {
            "id": 1,
            "timestamp": "2025-01-19T10:00:00",
            "mode": "MANUAL",
            "armed": 0,
            "location": {"lat": 32.0, "lon": 34.0, "alt": 10.0},
            "attitude": {"pitch": 0.1, "roll": 0.2, "yaw": 0.3},
            "groundspeed": 3.0
        }

        result = flight_service._format_telemetry(telemetry)

        assert result["armed"] is False
        assert result["altitude"] == 10.0

    def test_format_telemetry_with_invalid_json(self, flight_service):
        """Test _format_telemetry with invalid JSON strings."""
        telemetry = {
            "id": 1,
            "timestamp": "2025-01-19T10:00:00",
            "mode": "MANUAL",
            "armed": 0,
            "location": "not valid json",
            "attitude": "also not valid",
            "groundspeed": 0
        }

        result = flight_service._format_telemetry(telemetry)

        # Should return defaults on JSON parse error
        assert result["altitude"] == 0
        assert result["latitude"] == 0
        assert result["pitch"] == 0
