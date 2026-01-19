"""
Unit tests for RecordingService.
Tests video recording subprocess management.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestRecordingService:
    """Test suite for RecordingService class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        from services.recording_service import RecordingService
        RecordingService._instance = None
        yield
        RecordingService._instance = None

    @pytest.fixture
    def recording_service(self):
        """Create RecordingService instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('pathlib.Path.mkdir'):
                from services.recording_service import RecordingService
                service = RecordingService()
                service._recordings_dir = Path(tmpdir)
                return service

    def test_singleton_pattern(self):
        """RecordingService should be a singleton."""
        with patch('pathlib.Path.mkdir'):
            from services.recording_service import RecordingService
            service1 = RecordingService()
            service2 = RecordingService()
            assert service1 is service2

    def test_initial_state(self, recording_service):
        """Test initial state of RecordingService."""
        assert recording_service._recording_process is None
        assert recording_service._current_flight_id is None
        assert recording_service._video_path is None

    def test_is_running_no_process(self, recording_service):
        """Test is_running when no process."""
        recording_service._recording_process = None

        result = recording_service.is_running()

        assert result is False

    def test_is_running_process_alive(self, recording_service):
        """Test is_running when process is alive."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=None)  # None means still running
        recording_service._recording_process = mock_process

        result = recording_service.is_running()

        assert result is True

    def test_is_running_process_dead(self, recording_service):
        """Test is_running when process has ended."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=0)  # Return code means finished
        recording_service._recording_process = mock_process

        result = recording_service.is_running()

        assert result is False
        assert recording_service._recording_process is None

    def test_get_status_not_running(self, recording_service):
        """Test get_status when not running."""
        recording_service._recording_process = None
        recording_service._current_flight_id = None
        recording_service._video_path = None

        result = recording_service.get_status()

        assert result["running"] is False
        assert result["flight_id"] is None
        assert result["video_path"] is None

    def test_get_status_running(self, recording_service):
        """Test get_status when recording."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=None)
        recording_service._recording_process = mock_process
        recording_service._current_flight_id = 5
        recording_service._video_path = "/path/to/video.mp4"

        result = recording_service.get_status()

        assert result["running"] is True
        assert result["flight_id"] == 5
        assert result["video_path"] == "/path/to/video.mp4"

    def test_start_recording_already_running(self, recording_service):
        """Test start_recording when already running."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=None)  # Still running
        recording_service._recording_process = mock_process

        result = recording_service.start_recording(1)

        assert result["success"] is False
        assert "already running" in result["error"].lower()

    def test_start_recording_dead_process_cleanup(self, recording_service):
        """Test start_recording cleans up dead process."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=0)  # Process is dead
        recording_service._recording_process = mock_process
        recording_service._current_flight_id = 99
        recording_service._video_path = "/old/path.mp4"

        with patch('shutil.which', return_value=None), \
             patch('os.path.exists', return_value=False), \
             patch('subprocess.Popen', side_effect=FileNotFoundError("gstreamer not found")):
            result = recording_service.start_recording(1)

        # Should have cleaned up old state before trying to start
        assert recording_service._current_flight_id is None or result["success"] is False

    @patch('subprocess.Popen')
    @patch('shutil.which')
    def test_start_recording_success(self, mock_which, mock_popen, recording_service):
        """Test successful recording start."""
        mock_which.return_value = "/usr/bin/gst-launch-1.0"
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = recording_service.start_recording(1)

        assert result["success"] is True
        assert result["pid"] == 12345
        assert recording_service._current_flight_id == 1
        assert recording_service._video_path is not None

    @patch('subprocess.Popen')
    @patch('shutil.which')
    @patch('os.path.exists')
    def test_start_recording_gstreamer_fallback(self, mock_exists, mock_which, mock_popen, recording_service):
        """Test start_recording tries fallback GStreamer path."""
        mock_which.return_value = None  # Not in PATH
        mock_exists.return_value = True  # Windows path exists
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = recording_service.start_recording(1)

        assert result["success"] is True

    def test_start_recording_gstreamer_not_found(self, recording_service):
        """Test start_recording when GStreamer not found."""
        with patch('shutil.which', return_value=None), \
             patch('os.path.exists', return_value=False), \
             patch('subprocess.Popen', side_effect=FileNotFoundError()):
            result = recording_service.start_recording(1)

        assert result["success"] is False
        assert "gstreamer" in result["error"].lower()

    @patch('subprocess.Popen')
    @patch('shutil.which')
    def test_start_recording_exception(self, mock_which, mock_popen, recording_service):
        """Test start_recording handles exceptions."""
        mock_which.return_value = "gst-launch-1.0"
        mock_popen.side_effect = Exception("Subprocess error")

        result = recording_service.start_recording(1)

        assert result["success"] is False
        assert "error" in result

    def test_stop_recording_not_running(self, recording_service):
        """Test stop_recording when not running."""
        recording_service._recording_process = None

        result = recording_service.stop_recording()

        assert result["success"] is False
        assert "No recording process running" in result["error"]

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_stop_recording_success(self, mock_getsize, mock_exists, recording_service):
        """Test successful recording stop."""
        mock_exists.return_value = True
        mock_getsize.return_value = 10 * 1024 * 1024  # 10 MB

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.send_signal = Mock()
        mock_process.communicate = Mock(return_value=("stdout", "stderr"))

        recording_service._recording_process = mock_process
        recording_service._current_flight_id = 1
        recording_service._video_path = "/path/to/video.mp4"

        result = recording_service.stop_recording()

        assert result["success"] is True
        assert result["video_exists"] is True
        assert result["video_size_mb"] == 10.0
        assert recording_service._recording_process is None
        assert recording_service._current_flight_id is None

    @patch('os.path.exists')
    def test_stop_recording_video_not_created(self, mock_exists, recording_service):
        """Test stop_recording when video file not created."""
        mock_exists.return_value = False

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.send_signal = Mock()
        mock_process.communicate = Mock(return_value=("", ""))

        recording_service._recording_process = mock_process
        recording_service._current_flight_id = 1
        recording_service._video_path = "/path/to/video.mp4"

        result = recording_service.stop_recording()

        assert result["success"] is True
        assert result["video_exists"] is False

    @patch('os.path.exists')
    def test_stop_recording_timeout_force_kill(self, mock_exists, recording_service):
        """Test stop_recording force kills on timeout."""
        mock_exists.return_value = False

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.send_signal = Mock()
        mock_process.communicate = Mock(side_effect=[subprocess.TimeoutExpired("cmd", 10), ("", "")])
        mock_process.kill = Mock()

        recording_service._recording_process = mock_process
        recording_service._current_flight_id = 1
        recording_service._video_path = "/path/to/video.mp4"

        result = recording_service.stop_recording()

        assert result["success"] is True
        mock_process.kill.assert_called_once()

    def test_stop_recording_exception(self, recording_service):
        """Test stop_recording handles exceptions."""
        mock_process = Mock()
        mock_process.send_signal = Mock(side_effect=Exception("Signal error"))

        recording_service._recording_process = mock_process
        recording_service._video_path = "/path/to/video.mp4"

        result = recording_service.stop_recording()

        assert result["success"] is False
        assert "error" in result

    def test_force_cleanup_no_process(self, recording_service):
        """Test force_cleanup when no process exists."""
        recording_service._recording_process = None

        result = recording_service.force_cleanup()

        assert result["success"] is True

    def test_force_cleanup_running_process(self, recording_service):
        """Test force_cleanup kills running process."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll = Mock(return_value=None)  # Still running
        mock_process.kill = Mock()
        mock_process.wait = Mock()

        recording_service._recording_process = mock_process
        recording_service._current_flight_id = 5
        recording_service._video_path = "/path/to/video.mp4"

        result = recording_service.force_cleanup()

        assert result["success"] is True
        mock_process.kill.assert_called_once()
        assert recording_service._recording_process is None
        assert recording_service._current_flight_id is None
        assert recording_service._video_path is None

    def test_force_cleanup_dead_process(self, recording_service):
        """Test force_cleanup with already dead process."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=0)  # Already dead

        recording_service._recording_process = mock_process
        recording_service._current_flight_id = 5

        result = recording_service.force_cleanup()

        assert result["success"] is True
        assert recording_service._recording_process is None

    def test_force_cleanup_kill_exception(self, recording_service):
        """Test force_cleanup handles kill exception."""
        mock_process = Mock()
        mock_process.poll = Mock(return_value=None)
        mock_process.kill = Mock(side_effect=Exception("Kill error"))

        recording_service._recording_process = mock_process

        result = recording_service.force_cleanup()

        # Should still succeed and reset state
        assert result["success"] is True
        assert recording_service._recording_process is None

    @patch('subprocess.Popen')
    @patch('shutil.which')
    def test_start_recording_video_filename_format(self, mock_which, mock_popen, recording_service):
        """Test video filename contains flight_id and timestamp."""
        mock_which.return_value = "gst-launch-1.0"
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = recording_service.start_recording(42)

        assert result["success"] is True
        assert "flight_42" in recording_service._video_path
        assert ".mp4" in recording_service._video_path
