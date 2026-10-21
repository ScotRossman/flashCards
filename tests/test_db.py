from datetime import datetime

import pytest

from flashcardApp import db


class FakeCursor:
    def __init__(self, fetchone_results=(), fetchall_result=()):
        self.fetchone_results = iter(fetchone_results)
        self.fetchall_result = fetchall_result
        self.queries = []
        self.lastrowid = 24

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, parameters=None):
        self.queries.append((query, parameters))

    def fetchone(self):
        return next(self.fetchone_results, None)

    def fetchall(self):
        return self.fetchall_result


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.closed = True
        return False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        self.committed = True


def mock_connection(monkeypatch, cursor):
    connection = FakeConnection(cursor)
    options = {}

    def connect(**kwargs):
        options.update(kwargs)
        return connection

    monkeypatch.setattr(db.pymysql, "connect", connect)
    monkeypatch.setenv("DB_USER", "flashcards_app")
    monkeypatch.setenv("DB_PASSWORD", "test-password")
    return connection, options


def test_connect_uses_configured_endpoint_and_verifies_tls(monkeypatch):
    connection, options = mock_connection(monkeypatch, FakeCursor())
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_SSL_VERIFY_IDENTITY", "false")

    assert db._connect() is connection
    assert options["host"] == "127.0.0.1"
    assert options["port"] == 3307
    assert options["database"] == "flashcards"
    assert options["ssl"].verify_mode == db.ssl.CERT_REQUIRED
    assert options["ssl"].check_hostname is False


def test_connect_verifies_hostname_by_default(monkeypatch):
    _, options = mock_connection(monkeypatch, FakeCursor())
    monkeypatch.delenv("DB_SSL_VERIFY_IDENTITY", raising=False)

    db._connect()

    assert options["ssl"].verify_mode == db.ssl.CERT_REQUIRED
    assert options["ssl"].check_hostname is True


def test_init_db_checks_expected_tables(monkeypatch):
    cursor = FakeCursor()
    connection, _ = mock_connection(monkeypatch, cursor)

    db.init_db()

    assert len(cursor.queries) == 2
    assert "FROM players" in cursor.queries[0][0]
    assert "FROM sessions" in cursor.queries[1][0]
    assert connection.closed


def test_get_or_create_player_returns_existing_id(monkeypatch):
    cursor = FakeCursor()
    cursor.lastrowid = 12
    connection, _ = mock_connection(monkeypatch, cursor)

    assert db.get_or_create_player("Ada") == 12
    assert len(cursor.queries) == 1
    assert "ON DUPLICATE KEY UPDATE" in cursor.queries[0][0]
    assert connection.committed


def test_get_or_create_player_inserts_new_player(monkeypatch):
    cursor = FakeCursor()
    connection, _ = mock_connection(monkeypatch, cursor)

    assert db.get_or_create_player("Ada") == 24
    assert len(cursor.queries) == 1
    assert cursor.queries[0][1] == ("Ada",)
    assert connection.committed


def test_log_session_inserts_parameters_and_commits(monkeypatch):
    cursor = FakeCursor()
    connection, _ = mock_connection(monkeypatch, cursor)

    db.log_session(5, "addition", 3, 4)

    query, parameters = cursor.queries[0]
    assert "INSERT INTO sessions" in query
    assert parameters[:4] == (5, "addition", 3, 4)
    assert isinstance(parameters[4], datetime)
    assert connection.committed


def test_get_leaderboard_returns_mysql_rows(monkeypatch):
    rows = [("Ada", "addition", 3, 4, "2026-10-16 12:00:00")]
    cursor = FakeCursor(fetchall_result=rows)
    mock_connection(monkeypatch, cursor)

    assert db.get_leaderboard() == rows


def test_get_players_returns_mysql_rows(monkeypatch):
    rows = [(1, "Ada"), (2, "Grace")]
    cursor = FakeCursor(fetchall_result=rows)
    mock_connection(monkeypatch, cursor)

    assert db.get_players() == rows


def test_connection_requires_credentials(monkeypatch):
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="DB_USER and DB_PASSWORD"):
        db._connect()
