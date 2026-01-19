"""
Unit tests for DroneRepository.
Tests drone-related database operations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestDroneRepository:
    """Test suite for DroneRepository class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset class-level state before each test."""
        from database.drone_repository import DroneRepository
        DroneRepository._current_flight_id = None

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        mock = Mock()
        mock.execute_query = Mock(return_value=[])
        mock.execute_write = Mock(return_value=1)
        return mock

    @pytest.fixture
    def mock_flight_repo(self):
        """Create mock flight repository."""
        mock = Mock()
        mock.create_flight = Mock(return_value=1)
        mock.end_flight = Mock(return_value=True)
        return mock

    @pytest.fixture
    def drone_repo(self, mock_db, mock_flight_repo):
        """Create DroneRepository with mocked dependencies."""
        with patch('database.drone_repository.DatabaseConnection', return_value=mock_db), \
             patch('database.drone_repository.FlightRepository', return_value=mock_flight_repo):
            from database.drone_repository import DroneRepository
            repo = DroneRepository()
            repo.db = mock_db
            repo.flight_repository = mock_flight_repo
            return repo

    def test_get_current_flight_id_none(self, drone_repo):
        """Test get_current_flight_id when no flight is active."""
        result = drone_repo.get_current_flight_id()
        assert result is None

    def test_get_current_flight_id_with_flight(self, drone_repo):
        """Test get_current_flight_id when flight is active."""
        from database.drone_repository import DroneRepository
        DroneRepository._current_flight_id = 5

        result = drone_repo.get_current_flight_id()
        assert result == 5

    def test_start_flight(self, drone_repo, mock_flight_repo):
        """Test start_flight creates flight and stores ID."""
        mock_flight_repo.create_flight.return_value = 42

        result = drone_repo.start_flight()

        assert result == 42
        from database.drone_repository import DroneRepository
        assert DroneRepository._current_flight_id == 42
        mock_flight_repo.create_flight.assert_called_once()

    def test_end_flight_success(self, drone_repo, mock_flight_repo):
        """Test end_flight when flight is active."""
        from database.drone_repository import DroneRepository
        DroneRepository._current_flight_id = 10

        result = drone_repo.end_flight(pigeon_count=5)

        assert result is True
        mock_flight_repo.end_flight.assert_called_once_with(10, 5)
        assert DroneRepository._current_flight_id is None

    def test_end_flight_no_active_flight(self, drone_repo, mock_flight_repo):
        """Test end_flight when no flight is active."""
        from database.drone_repository import DroneRepository
        DroneRepository._current_flight_id = None

        result = drone_repo.end_flight(pigeon_count=0)

        assert result is False
        mock_flight_repo.end_flight.assert_not_called()

    def test_save_telemetry(self, drone_repo, mock_db):
        """Test save_telemetry stores telemetry data."""
        telemetry_data = {
            "mode": "GUIDED",
            "armed": True,
            "location": {"lat": 32.0, "lon": 34.0, "alt": 10.0},
            "attitude": {"pitch": 0.1, "roll": 0.2, "yaw": 0.3},
            "groundspeed": 5.0
        }

        result = drone_repo.save_telemetry(1, telemetry_data)

        assert result is True
        mock_db.execute_write.assert_called_once()
        call_args = mock_db.execute_write.call_args
        assert "INSERT INTO telemetry" in call_args[0][0]

    def test_save_telemetry_with_defaults(self, drone_repo, mock_db):
        """Test save_telemetry with missing data uses defaults."""
        telemetry_data = {}

        result = drone_repo.save_telemetry(1, telemetry_data)

        assert result is True
        call_args = mock_db.execute_write.call_args
        params = call_args[0][1]
        assert params[1] == "MANUAL"  # Default mode
        assert params[2] == 0  # Default armed (False -> 0)

    def test_get_flight_telemetry(self, drone_repo, mock_db):
        """Test get_flight_telemetry returns telemetry list."""
        mock_row1 = MagicMock()
        mock_row1.__iter__ = Mock(return_value=iter([("id", 1), ("groundspeed", 5.0)]))
        mock_row1.keys = Mock(return_value=["id", "groundspeed"])

        mock_db.execute_query.return_value = [
            {"id": 1, "timestamp": "2025-01-19", "groundspeed": 5.0},
            {"id": 2, "timestamp": "2025-01-19", "groundspeed": 6.0}
        ]

        result = drone_repo.get_flight_telemetry(1)

        assert len(result) == 2
        mock_db.execute_query.assert_called_once()
        assert "flight_id = ?" in mock_db.execute_query.call_args[0][0]

    def test_save_detection_image_success(self, drone_repo, mock_db):
        """Test save_detection_image on success."""
        result = drone_repo.save_detection_image(1, "/path/to/image.jpg")

        assert result is True
        mock_db.execute_write.assert_called_once()
        assert "INSERT INTO ditection_images" in mock_db.execute_write.call_args[0][0]

    def test_save_detection_image_failure(self, drone_repo, mock_db):
        """Test save_detection_image on database error."""
        mock_db.execute_write.side_effect = Exception("DB Error")

        result = drone_repo.save_detection_image(1, "/path/to/image.jpg")

        assert result is False

    def test_get_detection_images(self, drone_repo, mock_db):
        """Test get_detection_images returns image paths."""
        mock_db.execute_query.return_value = [
            {"image_path": "/path/to/image1.jpg"},
            {"image_path": "/path/to/image2.jpg"}
        ]

        result = drone_repo.get_detection_images(1)

        assert len(result) == 2
        assert "/path/to/image1.jpg" in result
        assert "/path/to/image2.jpg" in result

    def test_get_detection_images_empty(self, drone_repo, mock_db):
        """Test get_detection_images when no images exist."""
        mock_db.execute_query.return_value = []

        result = drone_repo.get_detection_images(1)

        assert result == []

    def test_save_video_recording_success(self, drone_repo, mock_db):
        """Test save_video_recording on success."""
        mock_db.execute_write.return_value = 1  # 1 row affected

        result = drone_repo.save_video_recording(1, "/path/to/video.mp4")

        assert result is True
        mock_db.execute_write.assert_called_once()
        assert "UPDATE flights" in mock_db.execute_write.call_args[0][0]

    def test_save_video_recording_no_rows_affected(self, drone_repo, mock_db):
        """Test save_video_recording when flight doesn't exist."""
        mock_db.execute_write.return_value = 0  # No rows affected

        result = drone_repo.save_video_recording(999, "/path/to/video.mp4")

        assert result is False

    def test_save_video_recording_failure(self, drone_repo, mock_db):
        """Test save_video_recording on database error."""
        mock_db.execute_write.side_effect = Exception("DB Error")

        result = drone_repo.save_video_recording(1, "/path/to/video.mp4")

        assert result is False

    def test_get_video_recordings_found(self, drone_repo, mock_db):
        """Test get_video_recordings when video exists."""
        mock_db.execute_query.return_value = [
            {"video_path": "/path/to/video.mp4"}
        ]

        result = drone_repo.get_video_recordings(1)

        assert len(result) == 1
        assert "/path/to/video.mp4" in result

    def test_get_video_recordings_not_found(self, drone_repo, mock_db):
        """Test get_video_recordings when no video exists."""
        mock_db.execute_query.return_value = []

        result = drone_repo.get_video_recordings(1)

        assert result == []

    def test_get_video_recordings_null_path(self, drone_repo, mock_db):
        """Test get_video_recordings when video_path is null."""
        mock_db.execute_query.return_value = [
            {"video_path": None}
        ]

        result = drone_repo.get_video_recordings(1)

        assert result == []
