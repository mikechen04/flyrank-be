"""Call the LLM with timeout, retries, and a cost log."""
import json
import os
import random
import time
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

PROMPT_VERSION = "triage-v1"
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "triage-v1.md"
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "cost.jsonl"
TIMEOUT_SECONDS = 30.0
MAX_ATTEMPTS = 3


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=TIMEOUT_SECONDS,
        max_retries=0,  # we retry in this file
    )


def _log_cost(model: str, usage, duration_ms: int, repaired: bool) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "prompt_version": PROMPT_VERSION,
                    "model": model,
                    "input_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                    "output_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                    "duration_ms": duration_ms,
                    "repaired": repaired,
                }
            )
            + "\n"
        )


def _should_retry(exc: Exception) -> bool:
    if isinstance(exc, (APITimeoutError, APIConnectionError, RateLimitError)):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code == 429 or exc.status_code >= 500
    return False


def _backoff(attempt: int, exc: Exception) -> None:
    wait = (2**attempt) + random.random()
    if isinstance(exc, APIStatusError) and exc.status_code == 429:
        header = (exc.response.headers or {}).get("retry-after")
        if header:
            try:
                wait = float(header)
            except ValueError:
                pass
    time.sleep(wait)


def complete(user_text: str, repair_note: str | None = None) -> str:
    model = os.environ["LLM_MODEL"]
    messages = [
        {"role": "system", "content": load_prompt()},
        {"role": "user", "content": json.dumps({"text": user_text})},
    ]
    if repair_note:
        messages.append({"role": "user", "content": repair_note})

    client = _client()
    for attempt in range(MAX_ATTEMPTS):
        started = time.time()
        try:
            res = client.chat.completions.create(
                model=model, messages=messages, temperature=0
            )
            _log_cost(
                model,
                res.usage,
                int((time.time() - started) * 1000),
                repaired=bool(repair_note),
            )
            return res.choices[0].message.content or ""
        except Exception as exc:
            if not _should_retry(exc) or attempt == MAX_ATTEMPTS - 1:
                raise
            _backoff(attempt, exc)
