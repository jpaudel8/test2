import json
import os
import sqlite3
from datetime import datetime, timezone

from app.config import DB_PATH


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                score REAL,
                detail_json TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_attempt(task_type: str, score: float, detail: dict) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO attempts (task_type, score, detail_json, created_at) VALUES (?, ?, ?, ?)",
            (task_type, score, json.dumps(detail), created_at),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "created_at": created_at}
    finally:
        conn.close()


def get_history(task_type: str = None, limit: int = 50) -> list:
    conn = _get_connection()
    try:
        if task_type:
            rows = conn.execute(
                "SELECT id, task_type, score, detail_json, created_at FROM attempts "
                "WHERE task_type = ? ORDER BY created_at DESC LIMIT ?",
                (task_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, task_type, score, detail_json, created_at FROM attempts "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "task_type": row["task_type"],
                    "score": row["score"],
                    "detail": json.loads(row["detail_json"]) if row["detail_json"] else None,
                    "created_at": row["created_at"],
                }
            )
        return result
    finally:
        conn.close()


def get_stats() -> list:
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT task_type, COUNT(*) as count, AVG(score) as avg_score "
            "FROM attempts GROUP BY task_type"
        ).fetchall()
        return [
            {
                "task_type": row["task_type"],
                "count": row["count"],
                "avg_score": row["avg_score"],
            }
            for row in rows
        ]
    finally:
        conn.close()
