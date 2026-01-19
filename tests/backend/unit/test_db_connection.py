"""
Unit tests for DatabaseConnection.
Tests SQLite connection management.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestDatabaseConnection:
    """Test suite for DatabaseConnection class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton before each test."""
        from database.db_connection import DatabaseConnection
        DatabaseConnection._instance = None

    def test_singleton_pattern(self):
        """DatabaseConnection should be a singleton."""
        from database.db_connection import DatabaseConnection

        db1 = DatabaseConnection()
        db2 = DatabaseConnection()

        assert db1 is db2

    @patch('sqlite3.connect')
    def test_connect_creates_connection(self, mock_connect):
        """Test that connect creates a new database connection."""
        from database.db_connection import DatabaseConnection

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db = DatabaseConnection()
        conn = db.connect()

        mock_connect.assert_called_once()
        assert conn is mock_conn
        assert mock_conn.row_factory == sqlite3.Row

    @patch('sqlite3.connect')
    def test_connect_returns_existing_connection(self, mock_connect):
        """Test that connect returns existing connection if already connected."""
        from database.db_connection import DatabaseConnection

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db = DatabaseConnection()
        conn1 = db.connect()
        conn2 = db.connect()

        # Should only call connect once
        assert mock_connect.call_count == 1
        assert conn1 is conn2

    @patch('sqlite3.connect')
    def test_disconnect(self, mock_connect):
        """Test disconnecting from database."""
        from database.db_connection import DatabaseConnection

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db = DatabaseConnection()
        db.connect()
        db.disconnect()

        mock_conn.close.assert_called_once()
        assert db.connection is None

    @patch('sqlite3.connect')
    def test_execute_query(self, mock_connect):
        """Test executing a SELECT query."""
        from database.db_connection import DatabaseConnection

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1}, {'id': 2}]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseConnection()
        result = db.execute_query("SELECT * FROM flights")

        mock_cursor.execute.assert_called_once_with("SELECT * FROM flights")
        assert result == [{'id': 1}, {'id': 2}]

    @patch('sqlite3.connect')
    def test_execute_query_with_params(self, mock_connect):
        """Test executing a SELECT query with parameters."""
        from database.db_connection import DatabaseConnection

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1}]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseConnection()
        result = db.execute_query("SELECT * FROM flights WHERE id = ?", (1,))

        mock_cursor.execute.assert_called_once_with("SELECT * FROM flights WHERE id = ?", (1,))
        assert len(result) == 1

    @patch('sqlite3.connect')
    def test_execute_write(self, mock_connect):
        """Test executing an INSERT query."""
        from database.db_connection import DatabaseConnection

        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 5
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseConnection()
        result = db.execute_write("INSERT INTO flights (start_time) VALUES (?)", ('2025-01-19',))

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        assert result == 5

    @patch('sqlite3.connect')
    def test_execute_many(self, mock_connect):
        """Test executing a query with multiple parameter sets."""
        from database.db_connection import DatabaseConnection

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseConnection()
        params = [('2025-01-19',), ('2025-01-20',)]
        db.execute_many("INSERT INTO flights (start_time) VALUES (?)", params)

        mock_cursor.executemany.assert_called_once_with(
            "INSERT INTO flights (start_time) VALUES (?)",
            params
        )
        mock_conn.commit.assert_called_once()
