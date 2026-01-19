"""
Unit tests for DetectionService.
Tests pigeon detection subprocess management.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import subprocess
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestDetectionService:
    """Test suite for DetectionService class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        from services.detection_service import DetectionService
        DetectionService._instance = None
        yield
        # Cleanup after test
        DetectionService._instance = None

    @pytest.fixture
    def mock_drone_repo(self):
        """Create mock drone repository."""
        mock = Mock()
        mock.save_detection_image = Mock(return_value=True)
        mock.save_video_recording = Mock(return_value=True)
        return mock

    @pytest.fixture
    def detection_service(self, mock_drone_repo):
        """Create DetectionService with mocked dependencies."""
        with patch('services.detection_service.DroneRepository', return_value=mock_drone_repo):
            from services.detection_service import DetectionService
            service = DetectionService()
            service._drone_repository = mock_drone_repo
            return service

    def test_singleton_pattern(self):
        """DetectionService should be a singleton."""
        with patch('services.detection_service.DroneRepository'):
            from services.detection_service import DetectionService
            service1 = DetectionService()
            service2 = DetectionService()
            assert service1 is service2

    def test_initial_state(self, detection_service):
        """Test initial state of DetectionService."""
        assert detection_service._detection_process is None
        assert detection_service._current_flight_id is None
        assert detection_service._detection_count == 0

    def test_is_running_no_process(self, detection_service):
        """Test is_running when no process."""
        detection_service._detection_process = None

        result = detection_service.is_running()

        assert result is False

    def test_is_running_process_alive(self, detection_service):
        """Test is_running when process is alive."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=None)  # None means still running
        detection_service._detection_process = mock_process

        result = detection_service.is_running()

        assert result is True

    def test_is_running_process_dead(self, detection_service):
        """Test is_running when process has ended."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=0)  # Return code means finished
        detection_service._detection_process = mock_process

        result = detection_service.is_running()

        assert result is False
        assert detection_service._detection_process is None

    def test_get_status(self, detection_service):
        """Test get_status returns current state."""
        detection_service._current_flight_id = 5
        detection_service._detection_count = 10

        result = detection_service.get_status()

        assert result["flight_id"] == 5
        assert result["detection_count"] == 10

    def test_start_detection_already_running(self, detection_service):
        """Test start_detection when already running."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=None)
        detection_service._detection_process = mock_process

        result = detection_service.start_detection(1)

        assert result["success"] is False
        assert "already running" in result["error"].lower()

    def test_start_detection_dead_process_cleanup(self, detection_service):
        """Test start_detection cleans up dead process reference."""
        from pathlib import Path

        mock_process = Mock()
        mock_process.poll = Mock(return_value=0)  # Process is dead
        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 99
        detection_service._detection_count = 50

        # Replace the script path with a mock
        mock_script = Mock(spec=Path)
        mock_script.exists.return_value = False
        detection_service._detection_script = mock_script

        result = detection_service.start_detection(1)

        # Should have cleaned up old state
        assert detection_service._detection_process is None
        assert result["success"] is False  # Script doesn't exist

    def test_start_detection_script_not_found(self, detection_service):
        """Test start_detection when script doesn't exist."""
        from pathlib import Path

        detection_service._detection_process = None

        mock_script = Mock(spec=Path)
        mock_script.exists.return_value = False
        detection_service._detection_script = mock_script

        result = detection_service.start_detection(1)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_start_detection_sdp_not_found(self, detection_service):
        """Test start_detection when SDP file doesn't exist."""
        from pathlib import Path
        import tempfile

        detection_service._detection_process = None

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a script file that exists
            script_path = Path(tmpdir) / "detect.py"
            script_path.touch()
            detection_service._detection_script = script_path

            # SDP file that doesn't exist
            detection_service._drone_sdp = Path(tmpdir) / "nonexistent.sdp"
            detection_service._project_root = Path(tmpdir)

            result = detection_service.start_detection(1)

        assert result["success"] is False
        assert "sdp" in result.get("error", "").lower() or "not found" in result.get("error", "").lower()

    @patch('subprocess.Popen')
    def test_start_detection_success(self, mock_popen, detection_service):
        """Test successful detection start."""
        from pathlib import Path
        import tempfile

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.stdout = Mock()
        mock_process.stdout.readline = Mock(return_value='')
        mock_popen.return_value = mock_process

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create script and SDP files
            script_path = Path(tmpdir) / "detect.py"
            script_path.touch()
            detection_service._detection_script = script_path

            sdp_path = Path(tmpdir) / "drone.sdp"
            sdp_path.touch()
            detection_service._drone_sdp = sdp_path
            detection_service._project_root = Path(tmpdir)

            result = detection_service.start_detection(1)

        assert result["success"] is True
        assert result["pid"] == 12345
        assert detection_service._current_flight_id == 1
        assert detection_service._detection_count == 0

    @patch('subprocess.Popen')
    def test_start_detection_exception(self, mock_popen, detection_service):
        """Test start_detection handles exceptions."""
        from pathlib import Path
        import tempfile

        mock_popen.side_effect = Exception("Subprocess error")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create script and SDP files
            script_path = Path(tmpdir) / "detect.py"
            script_path.touch()
            detection_service._detection_script = script_path

            sdp_path = Path(tmpdir) / "drone.sdp"
            sdp_path.touch()
            detection_service._drone_sdp = sdp_path
            detection_service._project_root = Path(tmpdir)

            result = detection_service.start_detection(1)

        assert result["success"] is False
        assert "error" in result

    def test_stop_detection_not_running(self, detection_service):
        """Test stop_detection when no process running."""
        detection_service._detection_process = None

        result = detection_service.stop_detection()

        assert result["success"] is False
        assert "No detection process running" in result["error"]

    def test_stop_detection_success(self, detection_service, mock_drone_repo):
        """Test successful detection stop."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.terminate = Mock()
        mock_process.communicate = Mock(return_value=("DETECTION_RESULT_JSON:{\"frames_processed\":100,\"detections_count\":5,\"total_pigeons\":8,\"frames_received\":500,\"duration_seconds\":60.0,\"average_fps\":1.67}", ""))
        mock_process.poll = Mock(return_value=None)

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._detection_count = 0
        detection_service._stdout_buffer = []
        detection_service._reader_thread = None

        result = detection_service.stop_detection()

        assert result["success"] is True
        assert result["frames_processed"] == 100
        assert result["detection_count"] == 5
        mock_process.terminate.assert_called_once()

    def test_stop_detection_with_image_paths(self, detection_service, mock_drone_repo):
        """Test stop_detection parses and saves image paths."""
        stdout = "DETECTION_IMAGE:/path/to/image1.jpg\nDETECTION_IMAGE:/path/to/image2.jpg\nDETECTION_RESULT_JSON:{}"

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.terminate = Mock()
        mock_process.communicate = Mock(return_value=(stdout, ""))

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._stdout_buffer = []
        detection_service._reader_thread = None

        result = detection_service.stop_detection()

        assert result["success"] is True
        assert mock_drone_repo.save_detection_image.call_count == 2

    def test_stop_detection_with_video_path(self, detection_service, mock_drone_repo):
        """Test stop_detection saves video path from JSON."""
        stdout = 'DETECTION_RESULT_JSON:{"video_file_path":"recordings/flight_1.mp4","frames_processed":50}'

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.terminate = Mock()
        mock_process.communicate = Mock(return_value=(stdout, ""))

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._stdout_buffer = []
        detection_service._reader_thread = None

        result = detection_service.stop_detection()

        assert result["success"] is True
        mock_drone_repo.save_video_recording.assert_called_once_with(1, "recordings/flight_1.mp4")

    def test_stop_detection_timeout_force_kill(self, detection_service):
        """Test stop_detection force kills on timeout."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.terminate = Mock()
        mock_process.communicate = Mock(side_effect=[subprocess.TimeoutExpired("cmd", 10), ("", "")])
        mock_process.kill = Mock()

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._stdout_buffer = []
        detection_service._reader_thread = None

        result = detection_service.stop_detection()

        assert result["success"] is True
        mock_process.kill.assert_called_once()

    def test_stop_detection_exception(self, detection_service):
        """Test stop_detection handles exceptions."""
        mock_process = Mock()
        mock_process.terminate = Mock(side_effect=Exception("Terminate error"))

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._stdout_buffer = []
        detection_service._reader_thread = None

        result = detection_service.stop_detection()

        assert result["success"] is False
        assert "error" in result.get("error", "").lower()

    def test_stop_detection_with_reader_thread(self, detection_service):
        """Test stop_detection waits for reader thread."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.terminate = Mock()
        mock_process.communicate = Mock(return_value=("", ""))

        mock_thread = Mock()
        mock_thread.is_alive = Mock(return_value=True)
        mock_thread.join = Mock()

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._stdout_buffer = []
        detection_service._reader_thread = mock_thread

        result = detection_service.stop_detection()

        mock_thread.join.assert_called_once_with(timeout=5)

    def test_stop_detection_uses_last_json_stats(self, detection_service):
        """Test stop_detection uses the last JSON stats line."""
        stdout = 'DETECTION_RESULT_JSON:{"frames_processed":10}\nDETECTION_RESULT_JSON:{"frames_processed":50}\nDETECTION_RESULT_JSON:{"frames_processed":100}'

        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.communicate = Mock(return_value=(stdout, ""))

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._stdout_buffer = []
        detection_service._reader_thread = None

        result = detection_service.stop_detection()

        # Should use the last JSON line (100 frames)
        assert result["frames_processed"] == 100

    def test_stop_detection_invalid_json(self, detection_service):
        """Test stop_detection handles invalid JSON."""
        stdout = 'DETECTION_RESULT_JSON:invalid json here'

        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.communicate = Mock(return_value=(stdout, ""))

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 1
        detection_service._stdout_buffer = []
        detection_service._reader_thread = None

        result = detection_service.stop_detection()

        # Should still succeed, just with default values
        assert result["success"] is True

    def test_force_cleanup_no_process(self, detection_service):
        """Test force_cleanup when no process exists."""
        detection_service._detection_process = None

        result = detection_service.force_cleanup()

        assert result["success"] is True

    def test_force_cleanup_running_process(self, detection_service):
        """Test force_cleanup kills running process."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll = Mock(return_value=None)  # Still running
        mock_process.kill = Mock()
        mock_process.wait = Mock()

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 5
        detection_service._detection_count = 10

        result = detection_service.force_cleanup()

        assert result["success"] is True
        mock_process.kill.assert_called_once()
        assert detection_service._detection_process is None
        assert detection_service._current_flight_id is None
        assert detection_service._detection_count == 0

    def test_force_cleanup_dead_process(self, detection_service):
        """Test force_cleanup with already dead process."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=0)  # Already dead

        detection_service._detection_process = mock_process
        detection_service._current_flight_id = 5

        result = detection_service.force_cleanup()

        assert result["success"] is True
        assert detection_service._detection_process is None

    def test_force_cleanup_kill_exception(self, detection_service):
        """Test force_cleanup handles kill exception."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=None)
        mock_process.kill = Mock(side_effect=Exception("Kill error"))

        detection_service._detection_process = mock_process

        result = detection_service.force_cleanup()

        # Should still succeed and reset state
        assert result["success"] is True
        assert detection_service._detection_process is None

    def test_start_drone_stream(self, detection_service):
        """Test start_drone_stream returns success message."""
        result = detection_service.start_drone_stream()

        assert result["success"] is True
        assert "manually" in result["message"].lower()

    def test_stop_drone_stream(self, detection_service):
        """Test stop_drone_stream returns success."""
        result = detection_service.stop_drone_stream()

        assert result["success"] is True

    def test_read_stdout_continuously_no_process(self, detection_service):
        """Test _read_stdout_continuously with no process."""
        detection_service._detection_process = None
        detection_service._stdout_buffer = []

        # Should return immediately without error
        detection_service._read_stdout_continuously()

        assert detection_service._stdout_buffer == []

    def test_read_stdout_continuously_with_output(self, detection_service):
        """Test _read_stdout_continuously reads lines."""
        mock_process = Mock()
        # Simulate reading lines then process ending
        mock_process.stdout.readline = Mock(side_effect=["line1\n", "line2\n", ""])
        mock_process.poll = Mock(side_effect=[None, None, 0])

        detection_service._detection_process = mock_process
        detection_service._stdout_buffer = []

        detection_service._read_stdout_continuously()

        assert "line1\n" in detection_service._stdout_buffer
        assert "line2\n" in detection_service._stdout_buffer

    def test_read_stdout_continuously_exception(self, detection_service):
        """Test _read_stdout_continuously handles exceptions."""
        mock_process = Mock()
        mock_process.stdout.readline = Mock(side_effect=Exception("Read error"))

        detection_service._detection_process = mock_process
        detection_service._stdout_buffer = []

        # Should not raise, just return
        detection_service._read_stdout_continuously()
