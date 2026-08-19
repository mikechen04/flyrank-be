"""SQLite job store. Poll GET /triage/jobs/{id} for status."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "jobs.db"


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    return datetime.now(timezone.utc).isoformat()


def init_jobs_db():
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            idempotency_key TEXT UNIQUE,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            input_json TEXT NOT NULL,
            result_json TEXT,
            error TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def create_job(kind: str, payload: dict, idempotency_key: str | None = None) -> dict:
    conn = _conn()
    if idempotency_key:
        row = conn.execute(
            "SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if row:
            conn.close()
            return dict(row)

    job_id = str(uuid.uuid4())
    now = _now()
    conn.execute(
        """
        INSERT INTO jobs
        (id, idempotency_key, kind, status, input_json, attempts, created_at, updated_at)
        VALUES (?, ?, ?, 'queued', ?, 0, ?, ?)
        """,
        (job_id, idempotency_key, kind, json.dumps(payload), now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row)


def get_job(job_id: str) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def mark_running(job_id: str) -> bool:
    """Claim a queued/retry job. Returns False if someone else already claimed it."""
    conn = _conn()
    cur = conn.execute(
        """
        UPDATE jobs
        SET status = 'running', attempts = attempts + 1, updated_at = ?
        WHERE id = ? AND status IN ('queued', 'retry')
        """,
        (_now(), job_id),
    )
    conn.commit()
    ok = cur.rowcount == 1
    conn.close()
    return ok


def mark_succeeded(job_id: str, result: dict) -> None:
    conn = _conn()
    conn.execute(
        """
        UPDATE jobs
        SET status = 'succeeded', result_json = ?, error = NULL, updated_at = ?
        WHERE id = ?
        """,
        (json.dumps(result), _now(), job_id),
    )
    conn.commit()
    conn.close()


def mark_failed(job_id: str, error: str, retry: bool) -> None:
    conn = _conn()
    conn.execute(
        """
        UPDATE jobs SET status = ?, error = ?, updated_at = ? WHERE id = ?
        """,
        ("retry" if retry else "failed", error, _now(), job_id),
    )
    conn.commit()
    conn.close()


def job_to_response(row: dict) -> dict:
    out = {
        "id": row["id"],
        "kind": row["kind"],
        "status": row["status"],
        "attempts": row["attempts"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if row.get("result_json"):
        out["result"] = json.loads(row["result_json"])
    if row.get("error"):
        out["error"] = row["error"]
    return out
