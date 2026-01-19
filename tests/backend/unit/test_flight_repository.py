"""
Unit tests for FlightRepository.
Tests database operations for flight records.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scarecrow-drone', 'backend'))


class TestFlightRepository:
    """Test suite for FlightRepository class."""

    @pytest.fixture
    def mock_db(self, mock_db_connection):
        """Setup mock database."""
        return mock_db_connection

    @pytest.fixture
    def flight_repository(self, mock_db):
        """Create FlightRepository with mocked database."""
        with patch('database.flight_repository.DatabaseConnection', return_value=mock_db):
            from database.flight_repository import FlightRepository
            repo = FlightRepository()
            repo.db = mock_db
            return repo

    def test_get_all_flights_empty(self, flight_repository, mock_db):
        """Test getting flights when database is empty."""
        mock_db.execute_query.return_value = []

        flights = flight_repository.get_all_flights()

        assert flights == []
        mock_db.execute_query.assert_called_once()

    def test_get_all_flights_with_data(self, flight_repository, mock_db):
        """Test getting flights with data."""
        # Create mock row
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            'flight_id': 1,
            'start_time': '2025-01-19T10:00:00',
            'end_time': '2025-01-19T10:05:00',
            'piegeon_detected': 3,
            'video_path': 'recordings/test.mp4'
        }.get(key)
        mock_row.keys.return_value = ['flight_id', 'start_time', 'end_time', 'piegeon_detected', 'video_path']

        mock_db.execute_query.return_value = [mock_row]

        flights = flight_repository.get_all_flights()

        assert len(flights) == 1
        assert flights[0]['id'] == '1'
        assert flights[0]['pigeons_detected'] == 3
        assert flights[0]['status'] == 'completed'

    def test_get_all_flights_in_progress(self, flight_repository, mock_db):
        """Test getting a flight that is in progress (no end_time)."""
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            'flight_id': 2,
            'start_time': '2025-01-19T10:00:00',
            'end_time': None,
            'piegeon_detected': 0,
            'video_path': None
        }.get(key)
        mock_row.keys.return_value = ['flight_id', 'start_time', 'end_time', 'piegeon_detected', 'video_path']

        mock_db.execute_query.return_value = [mock_row]

        flights = flight_repository.get_all_flights()

        assert len(flights) == 1
        assert flights[0]['status'] == 'in_progress'

    def test_get_flight_by_id_found(self, flight_repository, mock_db):
        """Test getting a specific flight by ID."""
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            'flight_id': 1,
            'start_time': '2025-01-19T10:00:00',
            'end_time': '2025-01-19T10:05:00',
            'piegeon_detected': 5,
            'video_path': None
        }.get(key)
        mock_row.keys.return_value = ['flight_id', 'start_time', 'end_time', 'piegeon_detected', 'video_path']

        mock_db.execute_query.return_value = [mock_row]

        flight = flight_repository.get_flight_by_id('1')

        assert flight is not None
        assert flight['id'] == '1'
        assert flight['pigeons_detected'] == 5

    def test_get_flight_by_id_not_found(self, flight_repository, mock_db):
        """Test getting a flight that doesn't exist."""
        mock_db.execute_query.return_value = []

        flight = flight_repository.get_flight_by_id('999')

        assert flight is None

    def test_create_flight(self, flight_repository, mock_db):
        """Test creating a new flight record."""
        mock_db.execute_write.return_value = 1

        flight_id = flight_repository.create_flight()

        assert flight_id == 1
        mock_db.execute_write.assert_called_once()
        # Verify the query contains INSERT
        call_args = mock_db.execute_write.call_args
        assert 'INSERT' in call_args[0][0]

    def test_end_flight(self, flight_repository, mock_db):
        """Test ending a flight."""
        mock_db.execute_write.return_value = 1

        result = flight_repository.end_flight(1, pigeon_count=5)

        assert result is True
        mock_db.execute_write.assert_called_once()
        # Verify UPDATE query
        call_args = mock_db.execute_write.call_args
        assert 'UPDATE' in call_args[0][0]
        # Verify pigeon count is passed
        assert 5 in call_args[0][1]

    def test_update_pigeon_count(self, flight_repository, mock_db):
        """Test updating pigeon count for a flight."""
        mock_db.execute_write.return_value = 1

        result = flight_repository.update_pigeon_count(1, 10)

        assert result is True
        mock_db.execute_write.assert_called_once()

    def test_delete_flight(self, flight_repository, mock_db):
        """Test deleting a flight record."""
        mock_db.execute_write.return_value = 1

        result = flight_repository.delete_flight(1)

        assert result is True
        mock_db.execute_write.assert_called_once()
        call_args = mock_db.execute_write.call_args
        assert 'DELETE' in call_args[0][0]

    def test_row_to_dict_duration_calculation(self, flight_repository, mock_db):
        """Test that duration is calculated correctly."""
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            'flight_id': 1,
            'start_time': '2025-01-19T10:00:00',
            'end_time': '2025-01-19T10:05:30',  # 5 minutes 30 seconds
            'piegeon_detected': 0,
            'video_path': None
        }.get(key)
        mock_row.keys.return_value = ['flight_id', 'start_time', 'end_time', 'piegeon_detected', 'video_path']

        result = flight_repository._row_to_dict(mock_row)

        assert result['duration'] == 330  # 5 min * 60 + 30 sec = 330 seconds

    def test_row_to_dict_time_extraction(self, flight_repository, mock_db):
        """Test that time portions are extracted correctly."""
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            'flight_id': 1,
            'start_time': '2025-01-19T14:30:45',
            'end_time': '2025-01-19T15:00:00',
            'piegeon_detected': 0,
            'video_path': None
        }.get(key)
        mock_row.keys.return_value = ['flight_id', 'start_time', 'end_time', 'piegeon_detected', 'video_path']

        result = flight_repository._row_to_dict(mock_row)

        assert result['start_time'] == '14:30:45'
        assert result['end_time'] == '15:00:00'
