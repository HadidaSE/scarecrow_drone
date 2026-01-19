"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime

# Add project paths to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, 'scarecrow-drone', 'backend')
DETECTION_PATH = os.path.join(PROJECT_ROOT, 'live_detection')

sys.path.insert(0, BACKEND_PATH)
sys.path.insert(0, DETECTION_PATH)


# ============================================================================
# Mock Fixtures for Drone Hardware
# ============================================================================

@pytest.fixture
def mock_subprocess():
    """Mock subprocess module for SSH/ping/command execution."""
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:

        # Default successful ping
        mock_run.return_value = Mock(
            returncode=0,
            stdout="connected",
            stderr=""
        )

        # Default successful process
        mock_popen.return_value = Mock(
            stdout=Mock(read=Mock(return_value=b'')),
            stderr=Mock(read=Mock(return_value='')),
            returncode=0,
            terminate=Mock(),
            wait=Mock(),
            kill=Mock()
        )

        yield {'run': mock_run, 'popen': mock_popen}


@pytest.fixture
def mock_drone_connected(mock_subprocess):
    """Simulate a connected drone via WiFi and SSH."""
    mock_subprocess['run'].return_value = Mock(
        returncode=0,
        stdout="CR_AP\nconnected",
        stderr=""
    )
    return mock_subprocess


@pytest.fixture
def mock_drone_disconnected(mock_subprocess):
    """Simulate a disconnected drone."""
    mock_subprocess['run'].return_value = Mock(
        returncode=1,
        stdout="",
        stderr="Connection refused"
    )
    return mock_subprocess


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    mock_db = Mock()
    mock_db.execute_query = Mock(return_value=[])
    mock_db.execute_write = Mock(return_value=1)
    mock_db.execute_many = Mock()
    mock_db.connect = Mock()
    mock_db.disconnect = Mock()
    return mock_db


@pytest.fixture
def sample_flight_data():
    """Sample flight data for testing."""
    return {
        'flight_id': 1,
        'start_time': '2025-01-19T10:00:00',
        'end_time': '2025-01-19T10:05:00',
        'piegeon_detected': 3,
        'video_path': 'recordings/flight_1_20250119_100000.mp4'
    }


@pytest.fixture
def sample_flight_row(sample_flight_data):
    """Mock database row for flight."""
    mock_row = Mock()
    mock_row.__getitem__ = lambda self, key: sample_flight_data.get(key)
    mock_row.keys = Mock(return_value=sample_flight_data.keys())
    return mock_row


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def mock_connection_service():
    """Mock ConnectionService for testing."""
    mock_service = Mock()
    mock_service.check_wifi_connection = Mock(return_value={"connected": True})
    mock_service.ping_drone = Mock(return_value=True)
    mock_service.connect_ssh = AsyncMock(return_value={"success": True})
    mock_service.disconnect_ssh = Mock(return_value={"success": True})
    mock_service.get_connection_status = Mock(return_value={
        "wifiConnected": True,
        "sshConnected": True,
        "droneReady": True
    })
    mock_service.is_ssh_connected = Mock(return_value=True)
    mock_service.start_video_stream = Mock(return_value={"success": True})
    mock_service.stop_video_stream = Mock(return_value={"success": True})
    mock_service.start_flight = Mock(return_value={"success": True, "output": "Flight started"})
    mock_service.return_home = Mock(return_value={"success": True})
    mock_service.abort_mission = Mock(return_value={"success": True})
    mock_service.MOCK_MODE = True
    return mock_service


@pytest.fixture
def mock_detection_service():
    """Mock DetectionService for testing."""
    mock_service = Mock()
    mock_service.start_detection = Mock(return_value={"success": True})
    mock_service.stop_detection = Mock(return_value={
        "success": True,
        "detection_count": 5,
        "frames_processed": 100
    })
    mock_service.is_running = Mock(return_value=False)
    return mock_service


@pytest.fixture
def mock_drone_repository():
    """Mock DroneRepository for testing."""
    mock_repo = Mock()
    mock_repo.start_flight = Mock(return_value=1)
    mock_repo.end_flight = Mock(return_value=True)
    mock_repo.get_current_flight_id = Mock(return_value=1)
    mock_repo.save_detection_image = Mock(return_value=True)
    return mock_repo


@pytest.fixture
def mock_flight_repository(sample_flight_data):
    """Mock FlightRepository for testing."""
    mock_repo = Mock()
    mock_repo.get_all_flights = Mock(return_value=[sample_flight_data])
    mock_repo.get_flight_by_id = Mock(return_value=sample_flight_data)
    mock_repo.create_flight = Mock(return_value=1)
    mock_repo.end_flight = Mock(return_value=True)
    mock_repo.update_pigeon_count = Mock(return_value=True)
    mock_repo.delete_flight = Mock(return_value=True)
    return mock_repo


# ============================================================================
# Detection/ML Fixtures
# ============================================================================

@pytest.fixture
def mock_yolo_model():
    """Mock YOLO model for testing detection."""
    mock_model = Mock()

    # Mock detection result
    mock_box = Mock()
    mock_box.xyxy = [Mock()]
    mock_box.xyxy[0].cpu = Mock(return_value=Mock(numpy=Mock(return_value=[100, 100, 200, 200])))
    mock_box.conf = [Mock()]
    mock_box.conf[0].cpu = Mock(return_value=Mock(numpy=Mock(return_value=0.85)))

    mock_result = Mock()
    mock_result.boxes = [mock_box]
    mock_result.plot = Mock(return_value=Mock())  # Returns annotated image

    mock_model.return_value = [mock_result]

    return mock_model


@pytest.fixture
def sample_frame():
    """Create a sample video frame for testing."""
    import numpy as np
    # Create a 640x480 BGR frame (black)
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_ffmpeg_process(sample_frame):
    """Mock ffmpeg process for video stream testing."""
    mock_process = Mock()
    mock_process.stdout = Mock()
    mock_process.stdout.read = Mock(return_value=sample_frame.tobytes())
    mock_process.stderr = Mock()
    mock_process.stderr.read = Mock(return_value='')
    mock_process.returncode = 0
    mock_process.terminate = Mock()
    mock_process.wait = Mock()
    return mock_process


# ============================================================================
# HTTP/API Fixtures
# ============================================================================

@pytest.fixture
def mock_fetch_response():
    """Mock fetch response for API testing."""
    def create_response(data, ok=True, status=200):
        mock_response = Mock()
        mock_response.ok = ok
        mock_response.status = status
        mock_response.json = AsyncMock(return_value=data)
        return mock_response
    return create_response
