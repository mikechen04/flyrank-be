"""Parse model text → JSON, validate, repair once, quarantine on fail."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from src.llm.client import PROMPT_VERSION, complete
from src.llm.schema import TriageOut

QUARANTINE = Path(__file__).resolve().parents[2] / "logs" / "quarantine.jsonl"
ParseError = (json.JSONDecodeError, ValidationError, TypeError, ValueError)


def _strip_fences(text: str) -> str:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if start != -1 and end > start else text


def parse_and_validate(raw: str) -> TriageOut:
    return TriageOut.model_validate(json.loads(_strip_fences(raw)))


def quarantine(raw: str, error: str) -> None:
    QUARANTINE.parent.mkdir(parents=True, exist_ok=True)
    with QUARANTINE.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "prompt_version": PROMPT_VERSION,
                    "error": error,
                    "raw": raw,
                }
            )
            + "\n"
        )


def run_triage(text: str) -> TriageOut:
    raw = complete(text)
    try:
        return parse_and_validate(raw)
    except ParseError as exc:
        raw2 = complete(
            text,
            repair_note=(
                f"Your previous answer was rejected for this reason: {exc}. "
                "Return only corrected JSON matching the schema."
            ),
        )
        try:
            return parse_and_validate(raw2)
        except ParseError as exc2:
            quarantine(raw2, str(exc2))
            raise ValueError(str(exc2)) from exc2
