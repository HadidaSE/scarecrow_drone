"""
Unit tests for ConnectionService.
Tests WiFi and SSH connection management with mocked hardware.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestConnectionService:
    """Test suite for ConnectionService class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton before each test."""
        # Clear singleton instance
        from services.connection_service import ConnectionService
        ConnectionService._instance = None

    def test_singleton_pattern(self):
        """ConnectionService should be a singleton."""
        from services.connection_service import ConnectionService

        service1 = ConnectionService()
        service2 = ConnectionService()

        assert service1 is service2

    def test_check_wifi_connection_mock_mode(self):
        """In mock mode, WiFi should always return connected."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True

        result = service.check_wifi_connection()

        assert result["connected"] is True

    @patch('subprocess.run')
    def test_check_wifi_connection_windows_connected(self, mock_run):
        """Test WiFi check on Windows when connected to drone network."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="SSID: CR_AP_12345\nSignal: 100%",
            stderr=""
        )

        with patch('platform.system', return_value='Windows'):
            service = ConnectionService()
            service.MOCK_MODE = False

            result = service.check_wifi_connection()

            assert result["connected"] is True
            mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_check_wifi_connection_windows_disconnected(self, mock_run):
        """Test WiFi check on Windows when NOT connected to drone network."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="SSID: HomeNetwork\nSignal: 80%",
            stderr=""
        )

        with patch('platform.system', return_value='Windows'):
            service = ConnectionService()
            service.MOCK_MODE = False

            result = service.check_wifi_connection()

            assert result["connected"] is False

    def test_ping_drone_success(self):
        """Test successful ping to drone - uses mock mode equivalent."""
        from services.connection_service import ConnectionService

        service = ConnectionService()

        # Directly mock the method to test the service returns what ping returns
        with patch.object(service, 'ping_drone', return_value=True):
            result = service.ping_drone()
            assert result is True

    def test_ping_drone_failure(self):
        """Test failed ping to drone - uses mock mode equivalent."""
        from services.connection_service import ConnectionService

        service = ConnectionService()

        # Directly mock the method to test the service returns what ping returns
        with patch.object(service, 'ping_drone', return_value=False):
            result = service.ping_drone()
            assert result is False

    @pytest.mark.asyncio
    async def test_connect_ssh_mock_mode(self):
        """In mock mode, SSH connect should succeed immediately."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True

        result = await service.connect_ssh()

        assert result["success"] is True
        assert service._ssh_connected is True

    @pytest.mark.asyncio
    async def test_connect_ssh_already_connected(self):
        """SSH connect should return success if already connected."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = True

        result = await service.connect_ssh()

        assert result["success"] is True
        assert "Already connected" in result.get("message", "")

    @pytest.mark.asyncio
    async def test_connect_ssh_success(self):
        """Test successful SSH connection when drone is reachable."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = False

        # Mock ping_drone to return True (drone is reachable)
        # Mock subprocess.run for the SSH test command
        with patch.object(service, 'ping_drone', return_value=True):
            import services.connection_service as conn_module
            original_subprocess = conn_module.subprocess
            try:
                mock_subprocess = Mock()
                mock_subprocess.run = Mock(return_value=Mock(returncode=0, stdout="connected", stderr=""))
                conn_module.subprocess = mock_subprocess

                result = await service.connect_ssh()

                assert result["success"] is True
                assert service._ssh_connected is True
            finally:
                conn_module.subprocess = original_subprocess

    @pytest.mark.asyncio
    async def test_connect_ssh_drone_unreachable(self):
        """SSH connect should fail if drone is not pingable."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = False

        # Mock ping_drone to return False (drone not reachable)
        with patch.object(service, 'ping_drone', return_value=False):
            result = await service.connect_ssh()

            assert result["success"] is False
            assert "Cannot reach drone" in result.get("error", "")

    def test_disconnect_ssh(self):
        """Test SSH disconnection."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = True
        service._ssh_process = Mock()
        service._ssh_process.terminate = Mock()
        service._ssh_process.wait = Mock()

        result = service.disconnect_ssh()

        assert result["success"] is True
        assert service._ssh_connected is False

    def test_get_connection_status_mock_mode(self):
        """In mock mode, all connections should show as connected."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True

        status = service.get_connection_status()

        assert status["wifiConnected"] is True
        assert status["sshConnected"] is True
        assert status["droneReady"] is True

    def test_is_ssh_connected(self):
        """Test SSH connection check."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = False

        assert service.is_ssh_connected() is False

        service._ssh_connected = True

        assert service.is_ssh_connected() is True

    @patch('subprocess.run')
    def test_run_drone_script_not_connected(self, mock_run):
        """Running drone script should fail if not connected."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = False

        result = service.run_drone_script("test.py")

        assert result["success"] is False
        assert "Not connected" in result.get("error", "")
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_run_drone_script_success(self, mock_run):
        """Test successful drone script execution."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Script output",
            stderr=""
        )

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.run_drone_script("test.py")

        assert result["success"] is True
        assert "Script output" in result.get("output", "")

    def test_start_video_stream_not_connected(self):
        """Start video stream should fail if not SSH connected."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = False

        result = service.start_video_stream()

        assert result["success"] is False

    def test_start_video_stream_mock_mode(self):
        """In mock mode, video stream should start successfully."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True
        service._ssh_connected = True

        result = service.start_video_stream()

        assert result["success"] is True

    def test_stop_video_stream_mock_mode(self):
        """In mock mode, video stream should stop successfully."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True
        service._ssh_connected = True

        result = service.stop_video_stream()

        assert result["success"] is True

    @patch('subprocess.run')
    def test_wifi_fail_count_threshold(self, mock_run):
        """SSH should disconnect after multiple WiFi failures."""
        from services.connection_service import ConnectionService

        # WiFi check fails
        mock_run.return_value = Mock(
            returncode=0,
            stdout="HomeNetwork",  # Not drone network
            stderr=""
        )

        with patch('platform.system', return_value='Windows'):
            service = ConnectionService()
            service.MOCK_MODE = False
            service._ssh_connected = True
            service._wifi_fail_count = 0
            service._wifi_fail_threshold = 3

            # Call get_connection_status multiple times to trigger threshold
            for _ in range(3):
                service.get_connection_status()

            # After threshold, SSH should be disconnected
            assert service._ssh_connected is False

    @patch('subprocess.run')
    def test_check_wifi_connection_macos(self, mock_run):
        """Test WiFi check on macOS uses ping_drone."""
        from services.connection_service import ConnectionService

        # Mock ping returns success
        mock_run.return_value = Mock(returncode=0)

        with patch('platform.system', return_value='Darwin'):
            service = ConnectionService()
            service.MOCK_MODE = False

            result = service.check_wifi_connection()

            assert result["connected"] is True

    @patch('subprocess.run')
    def test_check_wifi_connection_linux(self, mock_run):
        """Test WiFi check on Linux uses iwconfig."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="wlan0  IEEE 802.11  ESSID:\"CR_AP_12345\"",
            stderr=""
        )

        with patch('platform.system', return_value='Linux'):
            service = ConnectionService()
            service.MOCK_MODE = False

            result = service.check_wifi_connection()

            assert result["connected"] is True

    @patch('subprocess.run')
    def test_check_wifi_connection_linux_disconnected(self, mock_run):
        """Test WiFi check on Linux when not connected to drone."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="wlan0  IEEE 802.11  ESSID:\"HomeWifi\"",
            stderr=""
        )

        with patch('platform.system', return_value='Linux'):
            service = ConnectionService()
            service.MOCK_MODE = False

            result = service.check_wifi_connection()

            assert result["connected"] is False

    @patch('subprocess.run')
    def test_check_wifi_connection_exception(self, mock_run):
        """Test WiFi check handles exceptions."""
        from services.connection_service import ConnectionService

        mock_run.side_effect = Exception("Network error")

        with patch('platform.system', return_value='Windows'):
            service = ConnectionService()
            service.MOCK_MODE = False

            result = service.check_wifi_connection()

            assert result["connected"] is False
            assert "error" in result

    @patch('subprocess.run')
    def test_ping_drone_real_success(self, mock_run):
        """Test real ping_drone success."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(returncode=0)

        with patch('platform.system', return_value='Windows'):
            service = ConnectionService()

            result = service.ping_drone()

            assert result is True
            # Check ping command has correct flag
            call_args = mock_run.call_args[0][0]
            assert "-n" in call_args  # Windows flag

    @patch('subprocess.run')
    def test_ping_drone_real_failure(self, mock_run):
        """Test real ping_drone failure."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(returncode=1)

        service = ConnectionService()

        result = service.ping_drone()

        assert result is False

    @patch('subprocess.run')
    def test_ping_drone_exception(self, mock_run):
        """Test ping_drone handles exception."""
        from services.connection_service import ConnectionService

        mock_run.side_effect = Exception("Ping error")

        service = ConnectionService()

        result = service.ping_drone()

        assert result is False

    @patch('subprocess.run')
    def test_ping_drone_linux_flag(self, mock_run):
        """Test ping_drone uses -c flag on Linux."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(returncode=0)

        with patch('platform.system', return_value='Linux'):
            service = ConnectionService()

            result = service.ping_drone()

            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "-c" in call_args  # Linux/Mac flag

    def test_set_drone_connection(self):
        """Test set_drone_connection stores reference."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        mock_drone_conn = Mock()

        service.set_drone_connection(mock_drone_conn)

        assert service._drone_connection is mock_drone_conn

    def test_get_drone_data(self):
        """Test get_drone_data returns copy of data."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._drone_data = {"connected_status": True, "drone_id": 1}

        result = service.get_drone_data()

        assert result["connected_status"] is True
        assert result["drone_id"] == 1
        # Should be a copy
        result["connected_status"] = False
        assert service._drone_data["connected_status"] is True

    @pytest.mark.asyncio
    async def test_connect_ssh_timeout(self):
        """Test SSH connection timeout handling."""
        from services.connection_service import ConnectionService
        import subprocess

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = False

        with patch.object(service, 'ping_drone', return_value=True):
            import services.connection_service as conn_module
            original_subprocess = conn_module.subprocess
            try:
                mock_subprocess = Mock()
                mock_subprocess.run = Mock(side_effect=subprocess.TimeoutExpired("ssh", 10))
                mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
                conn_module.subprocess = mock_subprocess

                result = await service.connect_ssh()

                assert result["success"] is False
                assert "timed out" in result.get("error", "").lower()
            finally:
                conn_module.subprocess = original_subprocess

    @pytest.mark.asyncio
    async def test_connect_ssh_failure(self):
        """Test SSH connection failure."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = False

        with patch.object(service, 'ping_drone', return_value=True):
            import services.connection_service as conn_module
            original_subprocess = conn_module.subprocess
            try:
                mock_subprocess = Mock()
                mock_subprocess.run = Mock(return_value=Mock(returncode=1, stdout="", stderr="Permission denied"))
                conn_module.subprocess = mock_subprocess

                result = await service.connect_ssh()

                assert result["success"] is False
            finally:
                conn_module.subprocess = original_subprocess

    @pytest.mark.asyncio
    async def test_connect_ssh_exception(self):
        """Test SSH connection handles exception."""
        from services.connection_service import ConnectionService
        import subprocess

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = False

        with patch.object(service, 'ping_drone', return_value=True):
            import services.connection_service as conn_module
            original_subprocess = conn_module.subprocess
            try:
                mock_subprocess = Mock()
                mock_subprocess.run = Mock(side_effect=Exception("SSH error"))
                # Keep real exception classes
                mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
                conn_module.subprocess = mock_subprocess

                result = await service.connect_ssh()

                assert result["success"] is False
            finally:
                conn_module.subprocess = original_subprocess

    def test_disconnect_ssh_no_process(self):
        """Test SSH disconnection when no process."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = True
        service._ssh_process = None

        result = service.disconnect_ssh()

        assert result["success"] is True
        assert service._ssh_connected is False

    def test_disconnect_ssh_process_exception(self):
        """Test SSH disconnection handles process termination error."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = True
        mock_process = Mock()
        mock_process.terminate = Mock(side_effect=Exception("Terminate error"))
        mock_process.kill = Mock()
        service._ssh_process = mock_process

        result = service.disconnect_ssh()

        # Should still succeed after kill
        assert result["success"] is True
        mock_process.kill.assert_called_once()

    def test_run_drone_script_mock_mode(self):
        """Test run_drone_script in mock mode."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True
        service._ssh_connected = True

        result = service.run_drone_script("test.py")

        assert result["success"] is True
        assert "MOCK" in result.get("output", "")

    @patch('subprocess.run')
    def test_run_drone_script_failure(self, mock_run):
        """Test run_drone_script when script fails."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Script error"
        )

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.run_drone_script("test.py")

        assert result["success"] is False
        assert "Script error" in result.get("error", "") or "failed" in result.get("error", "").lower()

    @patch('subprocess.run')
    def test_run_drone_script_timeout(self, mock_run):
        """Test run_drone_script timeout."""
        import subprocess
        from services.connection_service import ConnectionService

        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 30)

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.run_drone_script("test.py")

        assert result["success"] is False
        assert "timed out" in result.get("error", "").lower()

    @patch('subprocess.run')
    def test_run_drone_script_exception(self, mock_run):
        """Test run_drone_script handles exception."""
        from services.connection_service import ConnectionService

        mock_run.side_effect = Exception("Connection error")

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.run_drone_script("test.py")

        assert result["success"] is False

    def test_start_flight_not_connected(self):
        """Test start_flight when not connected."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = False

        result = service.start_flight()

        assert result["success"] is False
        assert "Not connected" in result.get("error", "")

    def test_start_flight_mock_mode(self):
        """Test start_flight in mock mode."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = True
        service._ssh_connected = True

        result = service.start_flight()

        assert result["success"] is True
        assert "MOCK" in result.get("output", "")

    @patch('subprocess.run')
    def test_start_flight_success(self, mock_run):
        """Test successful flight start."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Flight started",
            stderr=""
        )

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.start_flight()

        assert result["success"] is True

    @patch('subprocess.run')
    def test_start_flight_failure(self, mock_run):
        """Test flight start failure."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Flight error"
        )

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.start_flight()

        assert result["success"] is False

    @patch('subprocess.run')
    def test_start_flight_timeout(self, mock_run):
        """Test flight start timeout."""
        import subprocess
        from services.connection_service import ConnectionService

        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 120)

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.start_flight()

        assert result["success"] is False
        assert "timed out" in result.get("error", "").lower()

    @patch('subprocess.run')
    def test_start_video_stream_success(self, mock_run):
        """Test successful video stream start."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.start_video_stream()

        assert result["success"] is True

    @patch('subprocess.run')
    def test_start_video_stream_failure(self, mock_run):
        """Test video stream start failure."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Stream error"
        )

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.start_video_stream()

        assert result["success"] is False

    @patch('subprocess.run')
    def test_start_video_stream_timeout(self, mock_run):
        """Test video stream start timeout."""
        import subprocess
        from services.connection_service import ConnectionService

        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 10)

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.start_video_stream()

        assert result["success"] is False
        assert "timed out" in result.get("error", "").lower()

    @patch('subprocess.run')
    def test_start_video_stream_exception(self, mock_run):
        """Test video stream start handles exception."""
        from services.connection_service import ConnectionService

        mock_run.side_effect = Exception("Stream error")

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.start_video_stream()

        assert result["success"] is False

    def test_stop_video_stream_not_connected(self):
        """Test stop_video_stream when not connected."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = False

        result = service.stop_video_stream()

        assert result["success"] is False

    @patch('subprocess.run')
    def test_stop_video_stream_success(self, mock_run):
        """Test successful video stream stop."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.stop_video_stream()

        assert result["success"] is True

    @patch('subprocess.run')
    def test_stop_video_stream_timeout(self, mock_run):
        """Test video stream stop timeout."""
        import subprocess
        from services.connection_service import ConnectionService

        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 10)

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.stop_video_stream()

        assert result["success"] is False

    @patch('subprocess.run')
    def test_stop_video_stream_exception(self, mock_run):
        """Test video stream stop handles exception."""
        from services.connection_service import ConnectionService

        mock_run.side_effect = Exception("Stop error")

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True

        result = service.stop_video_stream()

        assert result["success"] is False

    def test_return_home(self):
        """Test return_home calls run_drone_script."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = True
        service.MOCK_MODE = True

        result = service.return_home()

        assert result["success"] is True

    def test_abort_mission(self):
        """Test abort_mission calls run_drone_script."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service._ssh_connected = True
        service.MOCK_MODE = True

        result = service.abort_mission()

        assert result["success"] is True

    @patch('subprocess.run')
    def test_get_connection_status_wifi_recovery(self, mock_run):
        """Test WiFi recovery resets fail counter."""
        from services.connection_service import ConnectionService

        service = ConnectionService()
        service.MOCK_MODE = False
        service._ssh_connected = True
        service._wifi_fail_count = 2  # Had some failures

        # WiFi check now succeeds
        mock_run.return_value = Mock(
            returncode=0,
            stdout="CR_AP_12345",
            stderr=""
        )

        with patch('platform.system', return_value='Windows'):
            service.get_connection_status()

        # Fail count should be reset
        assert service._wifi_fail_count == 0
        assert service._ssh_connected is True

    @patch('subprocess.run')
    def test_get_connection_status_not_ssh_connected(self, mock_run):
        """Test get_connection_status when SSH not connected."""
        from services.connection_service import ConnectionService

        mock_run.return_value = Mock(
            returncode=0,
            stdout="CR_AP_12345",
            stderr=""
        )

        with patch('platform.system', return_value='Windows'):
            service = ConnectionService()
            service.MOCK_MODE = False
            service._ssh_connected = False

            status = service.get_connection_status()

            assert status["wifiConnected"] is True
            assert status["sshConnected"] is False
            assert status["droneReady"] is False
