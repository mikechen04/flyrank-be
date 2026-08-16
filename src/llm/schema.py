from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    feature = "feature"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class TriageIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class TriageOut(BaseModel):
    category: Category
    urgency: Urgency
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1, max_length=200)


STUB_ANSWER = TriageOut(
    category=Category.other,
    urgency=Urgency.normal,
    confidence=0.5,
    reason="Stub mode — no model call was made.",
)
