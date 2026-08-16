import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from openai import APIStatusError, APITimeoutError

from src.llm.parse import run_triage
from src.llm.schema import STUB_ANSWER, TriageIn

router = APIRouter()


def _err(status: int, message: str, **extra):
    return JSONResponse(status_code=status, content={"error": message, **extra})


@router.post("/triage", summary="Triage a support message")
def triage(body: TriageIn):
    """Classify a support message into category + urgency."""
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return _err(503, "LLM is disabled (LLM_ENABLED=false)")

    if os.getenv("LLM_STUB", "0") == "1":
        return STUB_ANSWER

    try:
        return run_triage(body.text)
    except APITimeoutError:
        return _err(504, "LLM timed out after 30 seconds")
    except APIStatusError as exc:
        if exc.status_code in (401, 403):
            return _err(401, "LLM auth failed — check LLM_API_KEY")
        return _err(502, f"LLM provider error: {exc.status_code}")
    except ValueError as exc:
        return _err(422, "model output failed validation", detail=str(exc))
