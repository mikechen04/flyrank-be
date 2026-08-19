"""Run triage jobs in the background. Retries on failure. Logs alerts if it finally fails."""
import json
import os
import time
from pathlib import Path

from openai import APIStatusError, APITimeoutError

from src.jobs.store import get_job, mark_failed, mark_running, mark_succeeded
from src.llm.parse import run_triage
from src.llm.schema import STUB_ANSWER

ALERTS = Path(__file__).resolve().parents[2] / "logs" / "alerts.jsonl"
MAX_ATTEMPTS = 3


def _alert(job_id: str, error: str, attempts: int) -> None:
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "level": "error",
                    "job_id": job_id,
                    "kind": "triage",
                    "attempts": attempts,
                    "error": error,
                }
            )
            + "\n"
        )


def process_triage_job(job_id: str) -> None:
    job = get_job(job_id)
    if not job or job["status"] in ("succeeded", "failed"):
        return
    if not mark_running(job_id):
        return

    job = get_job(job_id)
    text = json.loads(job["input_json"])["text"]

    try:
        if os.getenv("LLM_STUB", "0") == "1":
            result = STUB_ANSWER.model_dump()
        else:
            result = run_triage(text).model_dump()
        mark_succeeded(job_id, result)
        return
    except (APITimeoutError, APIStatusError, ValueError, RuntimeError) as exc:
        attempts = job["attempts"]
        can_retry = attempts < MAX_ATTEMPTS and not isinstance(exc, ValueError)
        if isinstance(exc, APIStatusError) and exc.status_code in (400, 401, 403):
            can_retry = False

        mark_failed(job_id, str(exc), retry=can_retry)
        if can_retry:
            time.sleep(2**attempts)
            process_triage_job(job_id)
        else:
            _alert(job_id, str(exc), attempts)
