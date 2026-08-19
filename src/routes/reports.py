import uuid

import inngest
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.inngest_app.client import inngest_client
from src.reports.store import reports

router = APIRouter()


class ReportIn(BaseModel):
    topic: str = Field(min_length=1)


@router.post("/reports", status_code=202, summary="Queue a report job")
async def create_report(body: ReportIn):
    """Accept now (202). Inngest does the slow work."""
    report_id = str(uuid.uuid4())
    reports[report_id] = {"id": report_id, "topic": body.topic, "status": "pending"}

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={"id": report_id, "topic": body.topic},
        )
    )

    return {"id": report_id, "status": "pending"}


@router.get("/reports/{report_id}", summary="Report status")
def get_report(report_id: str):
    report = reports.get(report_id)
    if not report:
        return JSONResponse(status_code=404, content={"error": "report not found"})
    return report
