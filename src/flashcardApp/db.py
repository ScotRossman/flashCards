import sqlite3
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

DB_NAME = "flashcards.db"
S3_BUCKET_NAME = "my-flashcard-tfstate-bucket"  # Replace with your S3 bucket name
S3_KEY = "flashcards.db"


def download_db_from_s3():
    """Downloads the database file from S3 on startup if it exists."""
    s3 = boto3.client("s3")
    try:
        s3.download_file(S3_BUCKET_NAME, S3_KEY, DB_NAME)
    except ClientError as e:
        # If the file doesn't exist in S3 yet, that's fine; a new one will be created.
        pass


def upload_db_to_s3():
    """Uploads the local database file back up to S3."""
    s3 = boto3.client("s3")
    try:
        s3.upload_file(DB_NAME, S3_BUCKET_NAME, S3_KEY)
    except ClientError as e:
        print(f"Error uploading to S3: {e}")


def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Players table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Practice sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            practice_type TEXT,
            score INTEGER,
            total_questions INTEGER,
            timestamp TEXT,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_player(name: str) -> int:
    """Gets an existing player's ID or creates a new player record."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM players WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        player_id = row[0]
    else:
        cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
        conn.commit()
        player_id = cursor.lastrowid

    conn.close()
    return player_id


def log_session(player_id: int, practice_type: str, score: int, total: int):
    """Logs a completed practice session."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO sessions (player_id, practice_type, score, total_questions, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """,
        (player_id, practice_type, score, total, timestamp),
    )

    conn.commit()
    conn.close()


def get_leaderboard():
    """Fetches past sessions joined with player names for display."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name, s.practice_type, s.score, s.total_questions, s.timestamp
        FROM sessions s
        JOIN players p ON s.player_id = p.id
        ORDER BY s.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
