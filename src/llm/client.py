"""Call the LLM with timeout, retries, and a simple cost log."""
import json
import os
import random
import time
from pathlib import Path

from src.llm.settings import MAX_ATTEMPTS, TIMEOUT_SECONDS
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

PROMPT_VERSION = "triage-v1"
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "triage-v1.md"
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "cost.jsonl"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=TIMEOUT_SECONDS,  # real timeout — do not rely on SDK default
        max_retries=0,  # we handle retries ourselves (see README)
    )


def _log_cost(model: str, usage, duration_ms: int, repaired: bool) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "input_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "output_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "duration_ms": duration_ms,
        "repaired": repaired,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def _should_retry(exc: Exception) -> bool:
    if isinstance(exc, (APITimeoutError, APIConnectionError, RateLimitError)):
        return True
    if isinstance(exc, APIStatusError):
        # retry 429 and 5xx only — never 400/401/403
        return exc.status_code == 429 or exc.status_code >= 500
    return False


def complete(user_text: str, repair_note: str | None = None) -> str:
    """One chat completion. Raises TimeoutError or API errors to the route."""
    model = os.environ["LLM_MODEL"]
    messages = [
        {"role": "system", "content": load_prompt()},
        {"role": "user", "content": json.dumps({"text": user_text})},
    ]
    if repair_note:
        messages.append({"role": "user", "content": repair_note})

    client = _client()
    last_exc = None
    for attempt in range(MAX_ATTEMPTS):
        started = time.time()
        try:
            res = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )
            duration_ms = int((time.time() - started) * 1000)
            _log_cost(model, res.usage, duration_ms, repaired=bool(repair_note))
            return res.choices[0].message.content or ""
        except Exception as exc:
            last_exc = exc
            if not _should_retry(exc) or attempt == MAX_ATTEMPTS - 1:
                raise
            # exponential backoff with jitter; honor Retry-After on 429 if present
            wait = (2**attempt) + random.random()
            if isinstance(exc, APIStatusError) and exc.status_code == 429:
                header = (exc.response.headers or {}).get("retry-after")
                if header:
                    try:
                        wait = float(header)
                    except ValueError:
                        pass
            time.sleep(wait)
    raise last_exc  # pragma: no cover
