import uuid
from datetime import datetime

from pydantic import BaseModel


class FactOut(BaseModel):
    id: uuid.UUID
    kind: str
    payload: dict
    confirmed_at: datetime | None
    source: str
    version: int

    class Config:
        from_attributes = True


class FactUpdate(BaseModel):
    payload: dict


class ResumeOut(BaseModel):
    id: uuid.UUID
    kind: str
    original_filename: str
    parsed_at: datetime | None
    is_base: bool

    class Config:
        from_attributes = True


class ResumeUploadResult(BaseModel):
    resume: ResumeOut
    candidate_facts: list[FactOut]
