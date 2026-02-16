"""Database adapter using local PostgreSQL.

Replaces Supabase client with direct PostgreSQL connections.
"""

import os
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Optional

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, RealDictRow

# Database connection pool
_connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None


def get_connection_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """Get or create the database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            # Fallback to individual env vars
            db_host = os.environ.get("DB_HOST", "localhost")
            db_port = os.environ.get("DB_PORT", "5432")
            db_name = os.environ.get("DB_NAME", "deepdiver")
            db_user = os.environ.get("DB_USER", "deepdiver")
            db_pass = os.environ.get("DB_PASSWORD", "deepdiver")
            database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url,
        )
    return _connection_pool


@contextmanager
def get_db_connection():
    """Get a database connection from the pool."""
    pool = get_connection_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


@contextmanager
def get_db_cursor(cursor_factory=RealDictCursor):
    """Get a database cursor with automatic connection management."""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


def execute_query(query: str, params: tuple = None) -> list[RealDictRow]:
    """Execute a SELECT query and return results."""
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_insert(query: str, params: tuple = None) -> str:
    """Execute an INSERT query and return the inserted ID."""
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()[0] if cursor.description else None


def execute_update(query: str, params: tuple = None) -> int:
    """Execute an UPDATE/DELETE query and return row count."""
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.rowcount


# ============================================================================
# Table Names
# ============================================================================
TABLES = {
    "scans": "scans",
    "scan_stocks": "scan_stocks",
    "settings": "settings",
    "alerts": "alerts",
    "earnings": "earnings",
    "positions": "positions",
    "covered_calls": "covered_calls",
    "routines": "routines",
    "watchlist": "watchlist",
    "journal": "journal",
}


# ============================================================================
# Generic CRUD Operations
# ============================================================================
def table_insert(table: str, data: dict) -> str:
    """Insert a row into a table."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
    return execute_insert(query, tuple(data.values()))


def table_select(table: str, where: str = None, params: tuple = None, order_by: str = None, limit: int = None) -> list[RealDictRow]:
    """Select rows from a table."""
    query = f"SELECT * FROM {table}"
    if where:
        query += f" WHERE {where}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {limit}"
    return execute_query(query, params)


def table_update(table: str, data: dict, where: str, params: tuple = None) -> int:
    """Update rows in a table."""
    set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {where}"
    full_params = tuple(data.values()) + (params or ())
    return execute_update(query, full_params)


def table_delete(table: str, where: str, params: tuple = None) -> int:
    """Delete rows from a table."""
    query = f"DELETE FROM {table} WHERE {where}"
    return execute_update(query, params)


# ============================================================================
# Health Check
# ============================================================================
def health_check() -> bool:
    """Check if database is accessible."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False
