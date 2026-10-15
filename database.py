"""
Database module for Mind Reader AI.
Handles SQLite database connection, table initialization, and CRUD operations
with parameterized queries for security and reliability.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mind_reader.db")


@contextmanager
def get_db_connection(db_path: Optional[str] = None):
    """Context manager for SQLite database connection."""
    target_path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables and indexes."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Players table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Game sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                game_mode TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
            );
            """
        )

        # Game rounds table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                previous_choices TEXT DEFAULT '[]',
                predicted_choice INTEGER,
                actual_choice INTEGER,
                prediction_correct INTEGER,
                confidence REAL DEFAULT 0.0,
                explanation TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE
            );
            """
        )

        # Indexes for fast query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_player ON game_sessions(player_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_session ON game_rounds(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_created ON game_rounds(created_at);")


def get_or_create_player(display_name: str = "Player", db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve an existing player or create a new one."""
    cleaned_name = display_name.strip() or "Player"
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE display_name = ? ORDER BY id ASC LIMIT 1;", (cleaned_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)

        cursor.execute("INSERT INTO players (display_name) VALUES (?);", (cleaned_name,))
        player_id = cursor.lastrowid
        return {"id": player_id, "display_name": cleaned_name, "created_at": datetime.now().isoformat()}


def create_session(player_id: int, game_mode: str, db_path: Optional[str] = None) -> int:
    """Create a new game session and return its ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO game_sessions (player_id, game_mode, score, current_streak, max_streak, started_at)
            VALUES (?, ?, 0, 0, 0, ?);
            """,
            (player_id, game_mode, datetime.now().isoformat()),
        )
        return int(cursor.lastrowid)


def get_session(session_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve session details by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game_sessions WHERE id = ?;", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_session(
    session_id: int,
    score: int,
    current_streak: int,
    max_streak: int,
    ended: bool = False,
    db_path: Optional[str] = None,
) -> bool:
    """Update session score, streak counts, and ended_at timestamp."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        ended_at = datetime.now().isoformat() if ended else None
        if ended:
            cursor.execute(
                """
                UPDATE game_sessions
                SET score = ?, current_streak = ?, max_streak = ?, ended_at = ?
                WHERE id = ?;
                """,
                (score, current_streak, max_streak, ended_at, session_id),
            )
        else:
            cursor.execute(
                """
                UPDATE game_sessions
                SET score = ?, current_streak = ?, max_streak = ?
                WHERE id = ?;
                """,
                (score, current_streak, max_streak, session_id),
            )
        return cursor.rowcount > 0


def record_round(
    session_id: int,
    round_number: int,
    previous_choices: str,
    predicted_choice: Optional[int],
    actual_choice: Optional[int],
    prediction_correct: bool,
    confidence: float,
    explanation: str,
    db_path: Optional[str] = None,
) -> int:
    """Record a round result in the game_rounds table."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO game_rounds (
                session_id, round_number, previous_choices,
                predicted_choice, actual_choice, prediction_correct,
                confidence, explanation, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                session_id,
                round_number,
                previous_choices,
                predicted_choice,
                actual_choice,
                1 if prediction_correct else 0,
                float(confidence),
                explanation,
                datetime.now().isoformat(),
            ),
        )
        return int(cursor.lastrowid)


def get_session_rounds(session_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all rounds recorded for a specific session."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM game_rounds
            WHERE session_id = ?
            ORDER BY round_number ASC;
            """,
            (session_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_recent_rounds(limit: int = 20, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve recent evaluated rounds across all sessions."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT gr.*, gs.game_mode, p.display_name
            FROM game_rounds gr
            JOIN game_sessions gs ON gr.session_id = gs.id
            JOIN players p ON gs.player_id = p.id
            WHERE gr.actual_choice IS NOT NULL
            ORDER BY gr.id DESC
            LIMIT ?;
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_overall_statistics(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute comprehensive game statistics.
    Handles empty data gracefully without division by zero.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Overall round counts
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_rounds,
                SUM(CASE WHEN prediction_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                SUM(CASE WHEN prediction_correct = 0 THEN 1 ELSE 0 END) as incorrect_count,
                AVG(confidence) as avg_confidence
            FROM game_rounds
            WHERE actual_choice IS NOT NULL;
            """
        )
        round_stats = dict(cursor.fetchone() or {})
        total_rounds = round_stats.get("total_rounds") or 0
        correct_count = round_stats.get("correct_count") or 0
        incorrect_count = round_stats.get("incorrect_count") or 0
        avg_confidence = round_stats.get("avg_confidence") or 0.0

        if total_rounds > 0:
            accuracy_rate = round((correct_count / total_rounds) * 100.0, 1)
        else:
            accuracy_rate = None

        # Highest score & max streak
        cursor.execute(
            """
            SELECT
                MAX(score) as max_score,
                MAX(max_streak) as longest_streak,
                COUNT(id) as total_sessions
            FROM game_sessions;
            """
        )
        session_stats = dict(cursor.fetchone() or {})
        max_score = session_stats.get("max_score") or 0
        longest_streak = session_stats.get("longest_streak") or 0
        total_sessions = session_stats.get("total_sessions") or 0

        # Mode breakdown
        cursor.execute(
            """
            SELECT
                gs.game_mode,
                COUNT(gr.id) as rounds_played,
                SUM(CASE WHEN gr.prediction_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM game_sessions gs
            LEFT JOIN game_rounds gr ON gs.id = gr.session_id AND gr.actual_choice IS NOT NULL
            GROUP BY gs.game_mode;
            """
        )
        mode_rows = cursor.fetchall()
        mode_stats = {}
        for row in mode_rows:
            mode = row["game_mode"]
            mode_rounds = row["rounds_played"] or 0
            mode_correct = row["correct_count"] or 0
            mode_acc = round((mode_correct / mode_rounds) * 100.0, 1) if mode_rounds > 0 else None
            mode_stats[mode] = {
                "rounds": mode_rounds,
                "correct": mode_correct,
                "accuracy": mode_acc,
            }

        return {
            "total_rounds": total_rounds,
            "correct_predictions": correct_count,
            "incorrect_predictions": incorrect_count,
            "accuracy_rate": accuracy_rate,
            "average_confidence": round(avg_confidence * 100.0, 1) if avg_confidence else None,
            "total_sessions": total_sessions,
            "highest_score": max_score,
            "longest_streak": longest_streak,
            "mode_stats": mode_stats,
            "recent_rounds": get_recent_rounds(10, db_path=db_path),
        }


def reset_all_data(db_path: Optional[str] = None) -> None:
    """Clear all recorded sessions and rounds for demo reset or testing."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM game_rounds;")
        cursor.execute("DELETE FROM game_sessions;")
        cursor.execute("DELETE FROM players;")
