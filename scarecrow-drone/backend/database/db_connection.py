import sqlite3
import os
from typing import Optional, List, Any


class DatabaseConnection:
    """SQLite database connection manager"""

    _instance: Optional['DatabaseConnection'] = None

    # Path to the database file
    DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'database',
        'scarecrow.db'
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establish database connection"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.DB_PATH, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: tuple = None) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()

    def execute_write(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return last row id"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.lastrowid

    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query with multiple parameter sets"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
