from datetime import datetime

from pydantic import BaseModel


class HardFilterSummary(BaseModel):
    scanned: int
    passed: int
    excluded_by_reason: dict[str, int]


class MatchedJobOut(BaseModel):
    job_id: str
    company_name: str
    title: str
    score: float
    limiting_factors: list[str]
    computed_at: datetime


class OpportunityReport(BaseModel):
    scanned: int
    passed_hard_filters: int
    excluded_by_reason: dict[str, int]
    met_quality_bar: int
    below_threshold: int
    threshold: float
    matched: list[MatchedJobOut]
    near_misses: list[MatchedJobOut]
