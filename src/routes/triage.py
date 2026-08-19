import os

from fastapi import APIRouter, BackgroundTasks, Header, Response
from fastapi.responses import JSONResponse

from src.jobs.store import create_job, get_job, job_to_response
from src.jobs.worker import process_triage_job
from src.llm.schema import TriageIn

router = APIRouter()


def _err(status: int, message: str):
    return JSONResponse(status_code=status, content={"error": message})


@router.post("/triage", status_code=202)
def triage(
    body: TriageIn,
    background_tasks: BackgroundTasks,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return _err(503, "LLM is disabled (LLM_ENABLED=false)")

    job = create_job("triage", {"text": body.text}, idempotency_key=idempotency_key)
    if job["status"] == "queued":
        background_tasks.add_task(process_triage_job, job["id"])

    status_url = f"/triage/jobs/{job['id']}"
    response.headers["Location"] = status_url
    return {
        "job_id": job["id"],
        "status": job["status"],
        "status_url": status_url,
    }


@router.get("/triage/jobs/{job_id}")
def triage_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return _err(404, "job not found")
    return job_to_response(job)
