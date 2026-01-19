# Scarecrow Drone Test Suite

Comprehensive test suite for the Scarecrow Drone pigeon detection system.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and mocks
├── pytest.ini                     # Pytest configuration
├── README.md                      # This file
├── backend/
│   ├── unit/
│   │   ├── test_connection_service.py  # WiFi/SSH connection tests
│   │   ├── test_drone_service.py       # Flight operations tests
│   │   ├── test_flight_repository.py   # Database operations tests
│   │   └── test_db_connection.py       # SQLite connection tests
│   └── integration/
│       ├── test_flight_flow.py         # End-to-end flight tests
│       └── test_api_endpoints.py       # FastAPI endpoint tests
└── detection/
    └── test_pigeon_detector.py         # ML detection tests
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -e ".[test]"
```

Or install directly:
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### Run All Tests

```bash
# From project root
cd scarecrow_drone
pytest tests/
```

### Run Specific Test Categories

```bash
# Backend unit tests only
pytest tests/backend/unit/

# Integration tests only
pytest tests/backend/integration/

# Detection/ML tests only
pytest tests/detection/

# Run a specific test file
pytest tests/backend/unit/test_drone_service.py

# Run a specific test
pytest tests/backend/unit/test_drone_service.py::TestDroneService::test_get_status
```

### Run with Coverage

```bash
pytest tests/ --cov=scarecrow-drone/backend --cov=live_detection --cov-report=html
```

Open `htmlcov/index.html` to view the coverage report.

### Run Frontend Tests

```bash
cd scarecrow-drone/frontend
npm test
```

## Test Categories

### Unit Tests
Fast, isolated tests that mock all external dependencies:
- `test_connection_service.py` - WiFi/SSH connection management
- `test_drone_service.py` - Flight start/stop/abort operations
- `test_flight_repository.py` - Flight database CRUD operations
- `test_db_connection.py` - SQLite database connection

### Integration Tests
Tests that verify multiple components working together:
- `test_flight_flow.py` - Complete flight lifecycle with mocked hardware
- `test_api_endpoints.py` - FastAPI endpoints with mocked services

### Detection Tests
Tests for the ML pigeon detection system:
- `test_pigeon_detector.py` - YOLO model integration, frame processing

## Mocking Strategy

Since we don't have the drone hardware during testing, all drone interactions are mocked:

1. **SSH/WiFi connections** - Mocked via `subprocess.run` patches
2. **Video stream** - Mocked via `subprocess.Popen` for ffmpeg
3. **YOLO model** - Mocked to return configurable detection results
4. **Database** - Uses in-memory SQLite or mocked connections

### Key Fixtures (conftest.py)

- `mock_subprocess` - Mocks all subprocess calls
- `mock_drone_connected` - Simulates connected drone
- `mock_drone_disconnected` - Simulates disconnected drone
- `mock_db_connection` - Mocks database operations
- `mock_connection_service` - Full ConnectionService mock
- `mock_detection_service` - Full DetectionService mock
- `mock_yolo_model` - Mocked YOLO model for detection
- `sample_frame` - Creates test video frames

## Writing New Tests

### Adding a Unit Test

```python
import pytest
from unittest.mock import Mock, patch

class TestMyService:
    @pytest.fixture
    def my_service(self, mock_dependency):
        # Setup service with mocked dependencies
        with patch('my_module.Dependency', return_value=mock_dependency):
            from my_module import MyService
            return MyService()

    def test_my_feature(self, my_service):
        result = my_service.do_something()
        assert result == expected_value
```

### Adding an Integration Test

```python
@pytest.mark.asyncio
async def test_complete_workflow(self, mock_subprocess, mock_database):
    # Test multiple components together
    from services.connection_service import ConnectionService
    from services.drone_service import DroneService

    conn = ConnectionService()
    conn.MOCK_MODE = True

    await conn.connect_ssh()
    # ... test the complete workflow
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
test:
  script:
    - pip install -e ".[test]"
    - pytest tests/ --cov --cov-report=xml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```
