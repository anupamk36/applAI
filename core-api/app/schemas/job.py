import uuid
from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    title: str
    seniority_band: str | None
    skills: list[str]
    exp_min: float | None
    exp_max: float | None
    ctc_min: float | None
    ctc_max: float | None
    locations: list[str]
    countries: list[str]
    remote_policy: str | None
    ats: str | None
    apply_url: str
    first_seen_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class CompanyOut(BaseModel):
    id: uuid.UUID
    canonical_name: str

    class Config:
        from_attributes = True


class JobListOut(BaseModel):
    items: list[JobOut]
    total: int
    limit: int
    offset: int
