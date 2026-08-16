import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from openai import APIStatusError, APITimeoutError
from pydantic import ValidationError

from src.llm.parse import run_triage
from src.llm.schema import STUB_ANSWER, TriageIn, TriageOut

router = APIRouter()


@router.post("/triage", summary="Triage a support message")
def triage(body: TriageIn):
    """Classify a support message into category + urgency."""
    # kill switch
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return JSONResponse(
            status_code=503,
            content={"error": "LLM is disabled (LLM_ENABLED=false)"},
        )

    # stub mode — no model call
    if os.getenv("LLM_STUB", "0") == "1":
        return TriageOut.model_validate(STUB_ANSWER)

    try:
        return run_triage(body.text)
    except APITimeoutError:
        return JSONResponse(
            status_code=504,
            content={"error": "LLM timed out after 30 seconds"},
        )
    except APIStatusError as exc:
        if exc.status_code in (401, 403):
            return JSONResponse(
                status_code=401,
                content={"error": "LLM auth failed — check LLM_API_KEY"},
            )
        return JSONResponse(
            status_code=502,
            content={"error": f"LLM provider error: {exc.status_code}"},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": "model output failed validation", "detail": str(exc)},
        )
    except ValidationError as exc:
        return JSONResponse(status_code=400, content={"error": exc.errors()})
