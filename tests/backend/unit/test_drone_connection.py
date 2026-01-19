"""
Unit tests for DroneConnection.
Tests WebSocket communication management for drone data.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestDroneConnection:
    """Test suite for DroneConnection class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton and class state before each test."""
        from services.drone_connection import DroneConnection
        DroneConnection._instance = None
        DroneConnection._drone_websocket = None
        DroneConnection._frontend_websockets = set()
        DroneConnection._status = {
            "is_connected": False,
            "is_flying": False,
            "mode": "MANUAL",
            "armed": False,
            "location": {},
            "attitude": {},
            "groundspeed": 0.0
        }
        yield
        DroneConnection._instance = None

    @pytest.fixture
    def drone_connection(self):
        """Create DroneConnection instance."""
        from services.drone_connection import DroneConnection
        return DroneConnection()

    def test_singleton_pattern(self):
        """DroneConnection should be a singleton."""
        from services.drone_connection import DroneConnection
        conn1 = DroneConnection()
        conn2 = DroneConnection()
        assert conn1 is conn2

    def test_initial_status(self, drone_connection):
        """Test initial status values."""
        status = drone_connection.get_status()

        assert status["is_connected"] is False
        assert status["is_flying"] is False
        assert status["mode"] == "MANUAL"
        assert status["armed"] is False

    def test_is_connected_false(self, drone_connection):
        """Test is_connected returns False initially."""
        result = drone_connection.is_connected()
        assert result is False

    def test_is_connected_true(self, drone_connection):
        """Test is_connected returns True when connected."""
        from services.drone_connection import DroneConnection
        DroneConnection._status["is_connected"] = True

        result = drone_connection.is_connected()
        assert result is True

    def test_is_flying_false(self, drone_connection):
        """Test is_flying returns False initially."""
        result = drone_connection.is_flying()
        assert result is False

    def test_is_flying_true(self, drone_connection):
        """Test is_flying returns True when flying."""
        from services.drone_connection import DroneConnection
        DroneConnection._status["is_flying"] = True

        result = drone_connection.is_flying()
        assert result is True

    def test_get_status_returns_copy(self, drone_connection):
        """Test get_status returns a copy of status."""
        status = drone_connection.get_status()

        # Modify the returned status
        status["is_connected"] = True

        # Original should be unchanged
        from services.drone_connection import DroneConnection
        assert DroneConnection._status["is_connected"] is False

    @pytest.mark.asyncio
    async def test_connect_drone(self, drone_connection):
        """Test connecting drone WebSocket."""
        from services.drone_connection import DroneConnection

        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()

        await drone_connection.connect_drone(mock_websocket)

        mock_websocket.accept.assert_called_once()
        assert DroneConnection._drone_websocket is mock_websocket
        assert DroneConnection._status["is_connected"] is True

    @pytest.mark.asyncio
    async def test_disconnect_drone(self, drone_connection):
        """Test disconnecting drone WebSocket."""
        from services.drone_connection import DroneConnection

        # Setup connected state
        DroneConnection._drone_websocket = AsyncMock()
        DroneConnection._status["is_connected"] = True
        DroneConnection._status["is_flying"] = True

        await drone_connection.disconnect_drone()

        assert DroneConnection._drone_websocket is None
        assert DroneConnection._status["is_connected"] is False
        assert DroneConnection._status["is_flying"] is False

    @pytest.mark.asyncio
    async def test_connect_frontend(self, drone_connection):
        """Test connecting frontend WebSocket."""
        from services.drone_connection import DroneConnection

        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()

        await drone_connection.connect_frontend(mock_websocket)

        mock_websocket.accept.assert_called_once()
        mock_websocket.send_json.assert_called_once()
        assert mock_websocket in DroneConnection._frontend_websockets

    def test_disconnect_frontend(self, drone_connection):
        """Test disconnecting frontend WebSocket."""
        from services.drone_connection import DroneConnection

        mock_websocket = Mock()
        DroneConnection._frontend_websockets.add(mock_websocket)

        drone_connection.disconnect_frontend(mock_websocket)

        assert mock_websocket not in DroneConnection._frontend_websockets

    def test_disconnect_frontend_not_connected(self, drone_connection):
        """Test disconnect_frontend when not connected (no error)."""
        mock_websocket = Mock()

        # Should not raise
        drone_connection.disconnect_frontend(mock_websocket)

    @pytest.mark.asyncio
    async def test_receive_drone_data(self, drone_connection):
        """Test receiving data from drone."""
        from services.drone_connection import DroneConnection

        data = {
            "mode": "GUIDED",
            "armed": True,
            "groundspeed": 5.0
        }

        await drone_connection.receive_drone_data(data)

        assert DroneConnection._status["mode"] == "GUIDED"
        assert DroneConnection._status["armed"] is True
        assert DroneConnection._status["groundspeed"] == 5.0
        assert DroneConnection._status["is_connected"] is True

    @pytest.mark.asyncio
    async def test_send_command_to_drone_success(self, drone_connection):
        """Test sending command to drone."""
        from services.drone_connection import DroneConnection

        mock_websocket = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        DroneConnection._drone_websocket = mock_websocket

        command = {"action": "takeoff", "altitude": 10}
        result = await drone_connection.send_command_to_drone(command)

        assert result is True
        mock_websocket.send_json.assert_called_once_with(command)

    @pytest.mark.asyncio
    async def test_send_command_to_drone_no_connection(self, drone_connection):
        """Test sending command when no drone connected."""
        from services.drone_connection import DroneConnection
        DroneConnection._drone_websocket = None

        command = {"action": "takeoff"}
        result = await drone_connection.send_command_to_drone(command)

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_to_frontends(self, drone_connection):
        """Test broadcasting to frontend WebSockets."""
        from services.drone_connection import DroneConnection

        mock_ws1 = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        DroneConnection._frontend_websockets = {mock_ws1, mock_ws2}

        data = {"status": "ok"}
        await drone_connection._broadcast_to_frontends(data)

        mock_ws1.send_json.assert_called_once_with(data)
        mock_ws2.send_json.assert_called_once_with(data)

    @pytest.mark.asyncio
    async def test_broadcast_to_frontends_removes_disconnected(self, drone_connection):
        """Test broadcast removes disconnected clients."""
        from services.drone_connection import DroneConnection

        mock_ws_good = AsyncMock()
        mock_ws_good.send_json = AsyncMock()

        mock_ws_bad = AsyncMock()
        mock_ws_bad.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        DroneConnection._frontend_websockets = {mock_ws_good, mock_ws_bad}

        await drone_connection._broadcast_to_frontends({"status": "ok"})

        # Bad websocket should be removed
        assert mock_ws_good in DroneConnection._frontend_websockets
        assert mock_ws_bad not in DroneConnection._frontend_websockets

    @pytest.mark.asyncio
    async def test_broadcast_to_frontends_empty(self, drone_connection):
        """Test broadcast with no frontends connected."""
        from services.drone_connection import DroneConnection
        DroneConnection._frontend_websockets = set()

        # Should not raise
        await drone_connection._broadcast_to_frontends({"status": "ok"})

    def test_update_status_from_ssh(self, drone_connection):
        """Test updating status from SSH subprocess."""
        from services.drone_connection import DroneConnection

        data = {
            "is_connected": True,
            "drone_id": 42
        }

        drone_connection.update_status_from_ssh(data)

        assert DroneConnection._status["is_connected"] is True
        assert DroneConnection._status["drone_id"] == 42

    def test_update_status_from_ssh_partial_data(self, drone_connection):
        """Test update_status_from_ssh with partial data."""
        from services.drone_connection import DroneConnection

        # Only connection status, no drone_id
        data = {"is_connected": False}

        drone_connection.update_status_from_ssh(data)

        assert DroneConnection._status["is_connected"] is False
        assert "drone_id" not in DroneConnection._status

    @pytest.mark.asyncio
    async def test_connect_drone_broadcasts_event(self, drone_connection):
        """Test connect_drone broadcasts to frontends."""
        from services.drone_connection import DroneConnection

        mock_frontend = AsyncMock()
        mock_frontend.send_json = AsyncMock()
        DroneConnection._frontend_websockets = {mock_frontend}

        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()

        await drone_connection.connect_drone(mock_websocket)

        # Should broadcast drone_connected event
        mock_frontend.send_json.assert_called()
        call_args = mock_frontend.send_json.call_args[0][0]
        assert call_args.get("event") == "drone_connected"

    @pytest.mark.asyncio
    async def test_disconnect_drone_broadcasts_event(self, drone_connection):
        """Test disconnect_drone broadcasts to frontends."""
        from services.drone_connection import DroneConnection

        mock_frontend = AsyncMock()
        mock_frontend.send_json = AsyncMock()
        DroneConnection._frontend_websockets = {mock_frontend}
        DroneConnection._drone_websocket = AsyncMock()

        await drone_connection.disconnect_drone()

        # Should broadcast drone_disconnected event
        mock_frontend.send_json.assert_called()
        call_args = mock_frontend.send_json.call_args[0][0]
        assert call_args.get("event") == "drone_disconnected"

    @pytest.mark.asyncio
    async def test_receive_drone_data_broadcasts(self, drone_connection):
        """Test receive_drone_data broadcasts to frontends."""
        from services.drone_connection import DroneConnection

        mock_frontend = AsyncMock()
        mock_frontend.send_json = AsyncMock()
        DroneConnection._frontend_websockets = {mock_frontend}

        await drone_connection.receive_drone_data({"mode": "AUTO"})

        mock_frontend.send_json.assert_called()
