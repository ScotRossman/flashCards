from datetime import datetime
from decimal import Decimal
import json
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from flashcardApp import db


class FakeCursor:
    def __init__(self, fetchone_results=(), fetchall_result=(), fetchall_results=None):
        self.fetchone_results = iter(fetchone_results)
        self.fetchall_result = fetchall_result
        self.fetchall_results = (
            iter(fetchall_results) if fetchall_results is not None else None
        )
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
        if self.fetchall_results is not None:
            return next(self.fetchall_results)
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

    pymysql = ModuleType("pymysql")
    pymysql.connect = connect
    monkeypatch.setitem(sys.modules, "pymysql", pymysql)
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


def test_connect_loads_credentials_from_secrets_manager(monkeypatch):
    _, options = mock_connection(monkeypatch, FakeCursor())
    monkeypatch.setenv(
        "DB_SECRET_ARN", "arn:aws:secretsmanager:region:account:secret:test"
    )
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    secrets_manager = ModuleType("boto3")
    secrets_client = Mock()
    secrets_client.get_secret_value.return_value = {
        "SecretString": json.dumps(
            {"username": "secret_user", "password": "secret_password"}
        )
    }
    secrets_manager.client = Mock(return_value=secrets_client)
    monkeypatch.setitem(sys.modules, "boto3", secrets_manager)

    db._connect()

    assert options["user"] == "secret_user"
    assert options["password"] == "secret_password"
    secrets_manager.client.assert_called_once_with("secretsmanager")
    secrets_client.get_secret_value.assert_called_once_with(
        SecretId="arn:aws:secretsmanager:region:account:secret:test"
    )


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


def test_get_database_overview_returns_stats_and_bounded_records(monkeypatch):
    cursor = FakeCursor(
        fetchone_results=[
            (Decimal("2"),),
            (Decimal("3"), Decimal("8"), Decimal("10")),
        ],
        fetchall_results=[
            [("addition", Decimal("2"), Decimal("5"), Decimal("6"))],
            [(Decimal("2"), "Grace"), (Decimal("1"), "Ada")],
            [
                (
                    Decimal("7"),
                    "Grace",
                    "addition",
                    Decimal("3"),
                    Decimal("4"),
                    "2026-10-22 12:00:00",
                )
            ],
        ],
    )
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "_connect", lambda: connection)

    overview = db.get_database_overview()

    assert overview["summary"] == {
        "players": 2,
        "sessions": 3,
        "correct_answers": 8,
        "questions_answered": 10,
        "accuracy_percent": 80.0,
    }
    assert overview["practice_stats"] == [
        {
            "practice_type": "addition",
            "sessions": 2,
            "correct_answers": 5,
            "questions_answered": 6,
        }
    ]
    assert overview["players"][0] == {"player_id": 2, "name": "Grace"}
    assert overview["recent_sessions"][0]["session_id"] == 7
    assert len(cursor.queries) == 5
    assert "LIMIT 100" in cursor.queries[3][0]
    assert "LIMIT 100" in cursor.queries[4][0]
    assert connection.closed
    json.dumps(overview)


def test_get_player_stats_returns_lifetime_and_practice_type_stats(monkeypatch):
    cursor = FakeCursor(
        fetchone_results=[
            (Decimal("42"), "Ada", Decimal("2"), Decimal("7"), Decimal("10"))
        ],
        fetchall_result=[("addition", Decimal("2"), Decimal("7"), Decimal("10"))],
    )
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "_connect", lambda: connection)

    stats = db.get_player_stats(42)

    assert stats == {
        "player": {"player_id": 42, "name": "Ada"},
        "summary": {
            "sessions": 2,
            "correct_answers": 7,
            "questions_answered": 10,
            "accuracy_percent": 70.0,
        },
        "practice_stats": [
            {
                "practice_type": "addition",
                "sessions": 2,
                "correct_answers": 7,
                "questions_answered": 10,
                "accuracy_percent": 70.0,
            }
        ],
    }
    assert cursor.queries[0][1] == (42,)
    assert cursor.queries[1][1] == (42,)
    assert "LEFT JOIN sessions" in cursor.queries[0][0]
    assert connection.closed
    json.dumps(stats)


def test_get_player_stats_returns_empty_totals_for_player_without_sessions(
    monkeypatch,
):
    cursor = FakeCursor(
        fetchone_results=[(Decimal("42"), "Ada", 0, 0, 0)],
        fetchall_result=[],
    )
    monkeypatch.setattr(db, "_connect", lambda: FakeConnection(cursor))

    stats = db.get_player_stats(42)

    assert stats["summary"] == {
        "sessions": 0,
        "correct_answers": 0,
        "questions_answered": 0,
        "accuracy_percent": 0.0,
    }
    assert stats["practice_stats"] == []


def test_get_player_stats_returns_none_for_unknown_player(monkeypatch):
    cursor = FakeCursor(fetchone_results=[None])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "_connect", lambda: connection)

    assert db.get_player_stats(999) is None
    assert len(cursor.queries) == 1
    assert connection.closed


def test_connection_requires_credentials(monkeypatch):
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="DB_USER and DB_PASSWORD"):
        db._connect()
