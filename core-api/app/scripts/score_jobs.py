"""Phase 1.5 manual trigger: `uv run python -m app.scripts.score_jobs`.

For each user: builds a candidate profile embedding from confirmed
fact_base text (one Voyage call per user, not cached — see plan's 1.5
note), runs every job through `evaluate_hard_filters()` (1.4b), and
soft-scores survivors via `compute_match_score()` (FR-402/403), upserting
`match_scores`. Also drives the calibration counter (FR-405): a job's
first time scoring >= threshold increments `calibration_count`, flipping
`calibration_complete` at 20.
"""

from datetime import datetime, timezone

from app.db import SessionLocal
from app.models.answer_bank import AnswerBankEntry
from app.models.fact_base import FactBase
from app.models.job import Company, Job
from app.models.match_score import MatchScore
from app.models.user import User, UserSettings
from app.services.embeddings import embed_query
from app.services.matching import evaluate_hard_filters
from app.services.scoring import compute_match_score

CALIBRATION_LIMIT = 20


def build_profile_text(db, user_id) -> str | None:
    facts = (
        db.query(FactBase)
        .filter(FactBase.user_id == user_id, FactBase.confirmed_at.isnot(None))
        .all()
    )
    if not facts:
        return None
    parts = [f.payload.get("name") or f.payload.get("raw_text") or "" for f in facts]
    text = "\n".join(p for p in parts if p)
    return text or None


def main():
    with SessionLocal() as db:
        for user in db.query(User).all():
            settings = db.get(UserSettings, user.id)
            if not settings:
                continue

            profile_text = build_profile_text(db, user.id)
            if not profile_text:
                print(f"[{user.email}] no confirmed facts yet, skipping")
                continue
            candidate_embedding = embed_query(profile_text)

            confirmed_skills = [
                f.payload.get("name")
                for f in db.query(FactBase).filter(
                    FactBase.user_id == user.id,
                    FactBase.kind == "skill",
                    FactBase.confirmed_at.isnot(None),
                )
                if f.payload.get("name")
            ]

            answers = {
                row.semantic_key: row.value
                for row in db.query(AnswerBankEntry).filter(AnswerBankEntry.user_id == user.id)
            }

            passed_hard_filter = scored = 0
            rows = db.query(Job, Company.canonical_name).join(Company, Company.id == Job.company_id)
            for job, company_name in rows:
                hf = evaluate_hard_filters(job, company_name, settings, answers)
                if not hf.passed:
                    continue
                passed_hard_filter += 1

                result = compute_match_score(job, candidate_embedding, settings, confirmed_skills)
                now = datetime.now(timezone.utc)

                existing = (
                    db.query(MatchScore)
                    .filter(MatchScore.user_id == user.id, MatchScore.job_id == job.id)
                    .first()
                )
                is_new = existing is None
                if existing:
                    existing.score = result.score
                    existing.factors = result.factors
                    existing.hard_filter_result = {"passed": True, "reason": None}
                    existing.computed_at = now
                    existing.threshold_at_time = settings.threshold
                else:
                    db.add(
                        MatchScore(
                            user_id=user.id,
                            job_id=job.id,
                            score=result.score,
                            factors=result.factors,
                            hard_filter_result={"passed": True, "reason": None},
                            computed_at=now,
                            threshold_at_time=settings.threshold,
                        )
                    )
                scored += 1

                if is_new and result.score >= settings.threshold and not settings.calibration_complete:
                    settings.calibration_count += 1
                    if settings.calibration_count >= CALIBRATION_LIMIT:
                        settings.calibration_complete = True

            db.commit()
            print(
                f"[{user.email}] passed_hard_filter={passed_hard_filter} scored={scored} "
                f"calibration_count={settings.calibration_count} "
                f"calibration_complete={settings.calibration_complete}"
            )


if __name__ == "__main__":
    main()
