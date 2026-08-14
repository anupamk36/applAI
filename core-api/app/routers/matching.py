"""Phase 1.4b verification surface (`/summary`) and Phase 1.5's Opportunity
Report data (`/opportunity-report`, §6.4). `/opportunity-report` needs
`match_scores` populated by `app/scripts/score_jobs.py` first — jobs that
passed hard filters but haven't been scored yet won't appear in either
bucket (not a bug, just "not scored yet").
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.answer_bank import AnswerBankEntry
from app.models.job import Company, Job
from app.models.match_score import MatchScore
from app.models.user import User, UserSettings
from app.schemas.matching import HardFilterSummary, MatchedJobOut, OpportunityReport
from app.services.auth import get_current_user
from app.services.matching import run_hard_filter_funnel

router = APIRouter(prefix="/matches", tags=["matching"])

NEAR_MISS_LIMIT = 20
MATCHED_LIMIT = 20


def _get_settings_and_answers(db: Session, user: User):
    settings = db.get(UserSettings, user.id)
    if not settings:
        settings = UserSettings(user_id=user.id)
    answers = {
        row.semantic_key: row.value
        for row in db.query(AnswerBankEntry).filter(AnswerBankEntry.user_id == user.id)
    }
    return settings, answers


@router.get("/summary", response_model=HardFilterSummary)
def hard_filter_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    settings, answers = _get_settings_and_answers(db, user)
    funnel = run_hard_filter_funnel(db, settings, answers)
    return HardFilterSummary(
        scanned=funnel.scanned, passed=funnel.passed, excluded_by_reason=funnel.excluded_by_reason
    )


def _limiting_factors(factors: dict, top_n: int = 2) -> list[str]:
    evaluated = [(key, f["value"]) for key, f in factors.items() if f["evaluated"]]
    evaluated.sort(key=lambda kv: kv[1])
    return [key for key, _ in evaluated[:top_n]]


def _to_matched_out(match: MatchScore, job: Job, company_name: str) -> MatchedJobOut:
    return MatchedJobOut(
        job_id=str(job.id),
        company_name=company_name,
        title=job.title,
        score=match.score,
        limiting_factors=_limiting_factors(match.factors),
        computed_at=match.computed_at,
    )


@router.get("/opportunity-report", response_model=OpportunityReport)
def opportunity_report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    settings, answers = _get_settings_and_answers(db, user)
    funnel = run_hard_filter_funnel(db, settings, answers)

    scored = (
        db.query(MatchScore, Job, Company.canonical_name)
        .join(Job, Job.id == MatchScore.job_id)
        .join(Company, Company.id == Job.company_id)
        .filter(MatchScore.user_id == user.id)
        .all()
    )

    matched_rows = sorted(
        (row for row in scored if row[0].score >= settings.threshold),
        key=lambda row: row[0].score,
        reverse=True,
    )
    near_miss_rows = sorted(
        (row for row in scored if row[0].score < settings.threshold),
        key=lambda row: row[0].score,
        reverse=True,
    )

    return OpportunityReport(
        scanned=funnel.scanned,
        passed_hard_filters=funnel.passed,
        excluded_by_reason=funnel.excluded_by_reason,
        met_quality_bar=len(matched_rows),
        below_threshold=len(near_miss_rows),
        threshold=settings.threshold,
        matched=[_to_matched_out(*row) for row in matched_rows[:MATCHED_LIMIT]],
        near_misses=[_to_matched_out(*row) for row in near_miss_rows[:NEAR_MISS_LIMIT]],
    )
