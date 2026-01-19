"""
Integration tests for the complete flight flow.
Tests the full cycle: connect -> start flight -> detect -> stop flight
All drone hardware is mocked.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestFlightFlowIntegration:
    """Integration tests for complete flight operations."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset all singleton instances before each test."""
        # Clear ConnectionService singleton
        from services.connection_service import ConnectionService
        ConnectionService._instance = None

        # Clear DatabaseConnection singleton
        from database.db_connection import DatabaseConnection
        DatabaseConnection._instance = None

    @pytest.fixture
    def mock_subprocess(self):
        """Mock all subprocess calls."""
        with patch('subprocess.run') as mock_run, \
             patch('subprocess.Popen') as mock_popen:

            # Successful responses by default
            mock_run.return_value = Mock(
                returncode=0,
                stdout="CR_AP\nconnected",
                stderr=""
            )

            mock_popen.return_value = Mock(
                stdout=Mock(read=Mock(return_value=b'')),
                stderr=Mock(read=Mock(return_value='')),
                returncode=0,
                terminate=Mock(),
                wait=Mock()
            )

            yield {'run': mock_run, 'popen': mock_popen}

    @pytest.fixture
    def mock_database(self):
        """Mock database operations."""
        with patch('database.db_connection.sqlite3') as mock_sqlite:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.lastrowid = 1
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_sqlite.connect.return_value = mock_conn

            yield {'connection': mock_conn, 'cursor': mock_cursor}

    @pytest.fixture
    def mock_detection(self):
        """Mock detection service."""
        with patch('services.detection_service.DetectionService') as mock_cls:
            mock_service = Mock()
            mock_service.start_detection = Mock(return_value={"success": True})
            mock_service.stop_detection = Mock(return_value={
                "success": True,
                "detection_count": 5,
                "frames_processed": 100
            })
            mock_service.is_running = Mock(return_value=False)
            mock_cls.return_value = mock_service
            yield mock_service

    @pytest.mark.asyncio
    async def test_complete_flight_cycle_mock_mode(self, mock_subprocess, mock_database):
        """Test complete flight cycle with mock mode enabled."""
        # Enable mock mode for hardware simulation
        from services.connection_service import ConnectionService
        from services.drone_service import DroneService

        # Setup connection service in mock mode
        conn_service = ConnectionService()
        conn_service.MOCK_MODE = True

        # Test connection flow
        assert conn_service.check_wifi_connection()["connected"] is True

        ssh_result = await conn_service.connect_ssh()
        assert ssh_result["success"] is True
        assert conn_service.is_ssh_connected() is True

        status = conn_service.get_connection_status()
        assert status["wifiConnected"] is True
        assert status["sshConnected"] is True
        assert status["droneReady"] is True

    @pytest.mark.asyncio
    async def test_flight_start_stop_with_detection(
        self, mock_subprocess, mock_database, mock_detection
    ):
        """Test flight start and stop with detection integration."""
        from services.connection_service import ConnectionService
        from services.drone_service import DroneService
        from services.detection_service import DetectionService

        # Setup connection
        conn_service = ConnectionService()
        conn_service.MOCK_MODE = True
        await conn_service.connect_ssh()

        # Patch DroneService dependencies
        with patch('services.drone_service.ConnectionService', return_value=conn_service), \
             patch('services.drone_service.DetectionService', return_value=mock_detection), \
             patch('services.drone_service.DroneRepository') as mock_repo_cls, \
             patch('services.drone_service.DroneConnection'):

            mock_repo = Mock()
            mock_repo.start_flight = Mock(return_value=1)
            mock_repo.end_flight = Mock(return_value=True)
            mock_repo.get_current_flight_id = Mock(return_value=1)
            mock_repo_cls.return_value = mock_repo

            drone_service = DroneService()
            drone_service.connection_service = conn_service
            drone_service.detection_service = mock_detection
            drone_service.drone_repository = mock_repo

            # Start flight
            start_result = await drone_service.start_flight()
            assert start_result["success"] is True
            assert start_result["flightId"] == "1"

            # Verify detection was started
            mock_detection.start_detection.assert_called_once_with(1)

            # Stop flight
            stop_result = await drone_service.stop_flight()
            assert stop_result["success"] is True
            assert stop_result["pigeonsDetected"] == 5
            assert stop_result["framesProcessed"] == 100

            # Verify detection was stopped
            mock_detection.stop_detection.assert_called_once()

            # Verify flight was ended in database
            mock_repo.end_flight.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_flight_abort_scenario(self, mock_subprocess, mock_database, mock_detection):
        """Test flight abort scenario."""
        from services.connection_service import ConnectionService
        from services.drone_service import DroneService

        conn_service = ConnectionService()
        conn_service.MOCK_MODE = True
        await conn_service.connect_ssh()

        with patch('services.drone_service.ConnectionService', return_value=conn_service), \
             patch('services.drone_service.DetectionService', return_value=mock_detection), \
             patch('services.drone_service.DroneRepository') as mock_repo_cls, \
             patch('services.drone_service.DroneConnection'):

            mock_repo = Mock()
            mock_repo.start_flight = Mock(return_value=2)
            mock_repo.end_flight = Mock(return_value=True)
            mock_repo.get_current_flight_id = Mock(return_value=2)
            mock_repo_cls.return_value = mock_repo

            # Update detection mock for abort
            mock_detection.stop_detection = Mock(return_value={
                "detection_count": 2,
                "frames_processed": 30
            })

            drone_service = DroneService()
            drone_service.connection_service = conn_service
            drone_service.detection_service = mock_detection
            drone_service.drone_repository = mock_repo

            # Start flight
            await drone_service.start_flight()

            # Abort flight
            abort_result = await drone_service.abort_mission()

            assert abort_result["success"] is True
            assert abort_result["pigeonsDetected"] == 2
            assert abort_result["framesProcessed"] == 30

    @pytest.mark.asyncio
    async def test_connection_loss_during_flight(self, mock_subprocess, mock_database):
        """Test handling of connection loss during flight."""
        from services.connection_service import ConnectionService

        conn_service = ConnectionService()
        conn_service.MOCK_MODE = False
        conn_service._ssh_connected = True

        # Simulate WiFi loss multiple times
        mock_subprocess['run'].return_value = Mock(
            returncode=0,
            stdout="HomeNetwork",  # Not drone network
            stderr=""
        )

        with patch('platform.system', return_value='Windows'):
            # Check status multiple times to trigger threshold
            for _ in range(conn_service._wifi_fail_threshold):
                conn_service.get_connection_status()

            # SSH should be disconnected after threshold
            assert conn_service._ssh_connected is False

    @pytest.mark.asyncio
    async def test_flight_without_ssh_connection(self, mock_database, mock_detection):
        """Test that flight fails without SSH connection."""
        from services.connection_service import ConnectionService
        from services.drone_service import DroneService

        conn_service = ConnectionService()
        conn_service._ssh_connected = False

        with patch('services.drone_service.ConnectionService', return_value=conn_service), \
             patch('services.drone_service.DetectionService', return_value=mock_detection), \
             patch('services.drone_service.DroneRepository') as mock_repo_cls, \
             patch('services.drone_service.DroneConnection'):

            mock_repo = Mock()
            mock_repo.start_flight = Mock(return_value=1)
            mock_repo_cls.return_value = mock_repo

            # Video stream should fail without SSH
            conn_service.start_video_stream = Mock(return_value={
                "success": False,
                "error": "Not connected to drone"
            })

            drone_service = DroneService()
            drone_service.connection_service = conn_service
            drone_service.detection_service = mock_detection
            drone_service.drone_repository = mock_repo

            result = await drone_service.start_flight()

            assert result["success"] is False


class TestAPIIntegration:
    """Integration tests for API endpoints with mocked services."""

    @pytest.fixture
    def mock_services(self):
        """Setup all mocked services."""
        with patch('services.connection_service.ConnectionService') as mock_conn_cls, \
             patch('services.drone_service.DroneService') as mock_drone_cls, \
             patch('database.flight_repository.FlightRepository') as mock_flight_cls:

            mock_conn = Mock()
            mock_conn.check_wifi_connection = Mock(return_value={"connected": True})
            mock_conn.connect_ssh = AsyncMock(return_value={"success": True})
            mock_conn.disconnect_ssh = Mock(return_value={"success": True})
            mock_conn.get_connection_status = Mock(return_value={
                "wifiConnected": True,
                "sshConnected": True,
                "droneReady": True
            })
            mock_conn_cls.return_value = mock_conn

            mock_drone = Mock()
            mock_drone.get_status = Mock(return_value={
                "isConnected": True,
                "isFlying": False
            })
            mock_drone.start_flight = AsyncMock(return_value={
                "success": True,
                "flightId": "1"
            })
            mock_drone.stop_flight = AsyncMock(return_value={
                "success": True,
                "pigeonsDetected": 5
            })
            mock_drone_cls.return_value = mock_drone

            mock_flight = Mock()
            mock_flight.get_all_flights = Mock(return_value=[
                {"id": "1", "date": "2025-01-19", "pigeons_detected": 5}
            ])
            mock_flight_cls.return_value = mock_flight

            yield {
                'connection': mock_conn,
                'drone': mock_drone,
                'flight': mock_flight
            }

    def test_mock_services_are_configured(self, mock_services):
        """Verify mock services are properly configured."""
        assert mock_services['connection'].check_wifi_connection()["connected"] is True
        assert mock_services['drone'].get_status()["isConnected"] is True
        assert len(mock_services['flight'].get_all_flights()) == 1


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    def in_memory_db(self):
        """Create an in-memory SQLite database for testing."""
        import sqlite3

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create flights table
        cursor.execute('''
            CREATE TABLE flights (
                flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                piegeon_detected INTEGER DEFAULT 0,
                video_path TEXT
            )
        ''')

        conn.commit()
        return conn

    def test_flight_lifecycle_in_database(self, in_memory_db):
        """Test complete flight lifecycle in database."""
        from datetime import datetime

        cursor = in_memory_db.cursor()

        # Start flight
        start_time = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO flights (start_time) VALUES (?)",
            (start_time,)
        )
        in_memory_db.commit()
        flight_id = cursor.lastrowid

        assert flight_id == 1

        # Verify flight is in progress
        cursor.execute(
            "SELECT * FROM flights WHERE flight_id = ?",
            (flight_id,)
        )
        row = cursor.fetchone()
        assert row['end_time'] is None
        assert row['piegeon_detected'] == 0

        # End flight
        end_time = datetime.now().isoformat()
        cursor.execute(
            "UPDATE flights SET end_time = ?, piegeon_detected = ? WHERE flight_id = ?",
            (end_time, 5, flight_id)
        )
        in_memory_db.commit()

        # Verify flight is complete
        cursor.execute(
            "SELECT * FROM flights WHERE flight_id = ?",
            (flight_id,)
        )
        row = cursor.fetchone()
        assert row['end_time'] is not None
        assert row['piegeon_detected'] == 5

    def test_multiple_flights(self, in_memory_db):
        """Test handling multiple flights."""
        from datetime import datetime

        cursor = in_memory_db.cursor()

        # Create 3 flights
        for i in range(3):
            start_time = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO flights (start_time, piegeon_detected) VALUES (?, ?)",
                (start_time, i * 2)
            )

        in_memory_db.commit()

        # Query all flights
        cursor.execute("SELECT * FROM flights ORDER BY flight_id")
        rows = cursor.fetchall()

        assert len(rows) == 3
        assert rows[0]['piegeon_detected'] == 0
        assert rows[1]['piegeon_detected'] == 2
        assert rows[2]['piegeon_detected'] == 4
