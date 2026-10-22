import json
import os
import ssl
from datetime import datetime

DB_HOST = "flashcard-1.c47iysguc25a.us-east-1.rds.amazonaws.com"
DB_PORT = 3306
DB_NAME = "flashcards"


def _environment_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"{name} must be true or false.")


def _connect():
    """Opens a TLS-protected connection to the configured MySQL database."""
    secret_arn = os.getenv("DB_SECRET_ARN")
    if secret_arn:
        import boto3

        secret_response = boto3.client("secretsmanager").get_secret_value(
            SecretId=secret_arn
        )
        secret = json.loads(secret_response["SecretString"])
        username = secret["username"]
        password = secret["password"]
    else:
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

    if not username or not password:
        raise RuntimeError("Configure DB_SECRET_ARN or set DB_USER and DB_PASSWORD.")

    import pymysql

    try:
        port = int(os.getenv("DB_PORT", str(DB_PORT)))
    except ValueError as error:
        raise ValueError("DB_PORT must be an integer.") from error

    ssl_ca = os.getenv("DB_SSL_CA")
    ssl_context = ssl.create_default_context(cafile=ssl_ca or None)
    ssl_context.check_hostname = _environment_flag(
        "DB_SSL_VERIFY_IDENTITY", default=True
    )

    connection_options = {
        "host": os.getenv("DB_HOST", DB_HOST),
        "port": port,
        "user": username,
        "password": password,
        "database": os.getenv("DB_NAME", DB_NAME),
        "charset": "utf8mb4",
        "ssl": ssl_context,
    }

    return pymysql.connect(**connection_options)


def init_db() -> None:
    """Checks the RDS connection and the app's expected tables."""
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM players LIMIT 0")
            cursor.execute("""
                SELECT id, player_id, practice_type, score, total_questions,
                       `timestamp`
                FROM sessions
                LIMIT 0
                """)


def get_or_create_player(name: str) -> int:
    """Gets an existing player's ID or creates a new player record."""
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO players (name) VALUES (%s)
                ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
                """,
                (name,),
            )
            player_id = cursor.lastrowid
        connection.commit()

    if player_id is None:
        raise RuntimeError("MySQL did not return an ID for the player.")
    return int(player_id)


def log_session(player_id: int, practice_type: str, score: int, total: int) -> None:
    """Logs a completed practice session."""
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sessions (
                    player_id, practice_type, score, total_questions, `timestamp`
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (player_id, practice_type, score, total, datetime.now()),
            )
        connection.commit()


def get_leaderboard() -> list[tuple]:
    """Fetches past sessions joined with player names for display."""
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.name, s.practice_type, s.score, s.total_questions,
                       s.`timestamp`
                FROM sessions s
                JOIN players p ON s.player_id = p.id
                ORDER BY s.id DESC
                """)
            return cursor.fetchall()


def get_players() -> list[tuple[int, str]]:
    """Fetches all registered players for display."""
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM players ORDER BY name")
            return cursor.fetchall()


def get_database_overview() -> dict:
    """Fetches aggregate stats and bounded samples of players and sessions."""
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(score), 0),
                       COALESCE(SUM(total_questions), 0)
                FROM sessions
                """)
            session_count, correct_answers, questions_answered = cursor.fetchone()

            cursor.execute("""
                SELECT practice_type, COUNT(*), COALESCE(SUM(score), 0),
                       COALESCE(SUM(total_questions), 0)
                FROM sessions
                GROUP BY practice_type
                ORDER BY practice_type
                """)
            practice_stats = [
                {
                    "practice_type": practice_type,
                    "sessions": int(sessions),
                    "correct_answers": int(correct),
                    "questions_answered": int(total),
                }
                for practice_type, sessions, correct, total in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT id, name
                FROM players
                ORDER BY id DESC
                LIMIT 100
                """)
            players = [
                {"player_id": int(player_id), "name": name}
                for player_id, name in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT s.id, p.name, s.practice_type, s.score,
                       s.total_questions,
                       DATE_FORMAT(s.`timestamp`, '%Y-%m-%d %H:%i:%s')
                FROM sessions s
                JOIN players p ON p.id = s.player_id
                ORDER BY s.`timestamp` DESC, s.id DESC
                LIMIT 100
                """)
            recent_sessions = [
                {
                    "session_id": int(session_id),
                    "player_name": player_name,
                    "practice_type": practice_type,
                    "score": int(score),
                    "total_questions": int(total),
                    "timestamp": timestamp,
                }
                for (
                    session_id,
                    player_name,
                    practice_type,
                    score,
                    total,
                    timestamp,
                ) in cursor.fetchall()
            ]

    return {
        "summary": {
            "players": int(player_count),
            "sessions": int(session_count),
            "correct_answers": int(correct_answers),
            "questions_answered": int(questions_answered),
            "accuracy_percent": (
                round(int(correct_answers) / int(questions_answered) * 100, 1)
                if questions_answered
                else 0.0
            ),
        },
        "practice_stats": practice_stats,
        "players": players,
        "recent_sessions": recent_sessions,
    }
