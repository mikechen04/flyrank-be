"""Parse model text → JSON, validate with schema, repair once, quarantine on fail."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from src.llm.client import PROMPT_VERSION, complete
from src.llm.schema import TriageOut

QUARANTINE = Path(__file__).resolve().parents[2] / "logs" / "quarantine.jsonl"


def _strip_fences(text: str) -> str:
    text = text.strip()
    # remove ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    # find first { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_and_validate(raw: str) -> TriageOut:
    cleaned = _strip_fences(raw)
    data = json.loads(cleaned)
    return TriageOut.model_validate(data)


def quarantine(raw: str, error: str) -> None:
    QUARANTINE.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "error": error,
        "raw": raw,
    }
    with QUARANTINE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def run_triage(text: str) -> TriageOut:
    raw = complete(text)
    try:
        return parse_and_validate(raw)
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        note = (
            "Your previous answer was rejected for this reason: "
            f"{exc}. Return only corrected JSON matching the schema."
        )
        raw2 = complete(text, repair_note=note)
        try:
            return parse_and_validate(raw2)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc2:
            quarantine(raw2, str(exc2))
            raise ValueError(str(exc2)) from exc2
