"""Phase 1.4c manual trigger: `uv run python -m app.scripts.score_ghost_jobs`.

Recomputes `jobs.ghost_score` for every job. Idempotent, rerunnable —
same pattern as ingest.run / embed_jobs.py.
"""

from sqlalchemy import func

from app.db import SessionLocal
from app.models.job import Job
from app.services.ghost_scoring import compute_ghost_score


def main():
    with SessionLocal() as db:
        latest_ingest_at = db.query(func.max(Job.last_seen_at)).scalar()
        if latest_ingest_at is None:
            print("No jobs to score.")
            return

        jobs = db.query(Job).all()
        counts = {"active": 0, "delisted": 0, "evergreen": 0}
        for job in jobs:
            result = compute_ghost_score(job, latest_ingest_at)
            job.ghost_score = result.score
            counts[result.reason] += 1

        db.commit()
        print(f"Scored {len(jobs)} jobs against latest_ingest_at={latest_ingest_at}: {counts}")


if __name__ == "__main__":
    main()
