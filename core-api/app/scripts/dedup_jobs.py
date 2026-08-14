"""Phase 1.4c manual trigger: `uv run python -m app.scripts.dedup_jobs`.

Post-hoc merge pass (not at-ingestion) — see plan's Phase 1.4c note on why:
worker-ingest persists jobs synchronously without embeddings (separate
venv, no Voyage call), embeddings land later via embed_jobs.py. This
script runs after embeddings exist and collapses same-company near-
duplicates (FR-305) into one Job with multiple JobSource rows, keeping
the earliest-first-seen Job as canonical.
"""

import uuid

from sqlalchemy import select

from app.db import SessionLocal
from app.models.job import Job, JobSource
from app.services.dedup import is_likely_duplicate

CANDIDATES_PER_JOB = 10


def main():
    with SessionLocal() as db:
        jobs = (
            db.query(Job)
            .filter(Job.jd_embedding.isnot(None))
            .order_by(Job.first_seen_at)
            .all()
        )
        merged_ids: set[uuid.UUID] = set()
        merges = 0

        for job in jobs:
            if job.id in merged_ids:
                continue

            dist_expr = Job.jd_embedding.cosine_distance(job.jd_embedding).label("distance")
            stmt = (
                select(Job, dist_expr)
                .where(
                    Job.company_id == job.company_id,
                    Job.id != job.id,
                    Job.jd_embedding.isnot(None),
                )
                .order_by(dist_expr)
                .limit(CANDIDATES_PER_JOB)
            )
            candidates = db.execute(stmt).all()

            for cand, distance in candidates:
                if cand.id in merged_ids:
                    continue
                if not is_likely_duplicate(job, cand, distance):
                    continue

                canonical, duplicate = (
                    (job, cand) if job.first_seen_at <= cand.first_seen_at else (cand, job)
                )
                db.query(JobSource).filter(JobSource.job_id == duplicate.id).update(
                    {"job_id": canonical.id}
                )
                db.delete(duplicate)
                merged_ids.add(duplicate.id)
                merges += 1
                print(f"Merged '{duplicate.title}' -> '{canonical.title}' ({canonical.id})")

                if duplicate.id == job.id:
                    break  # job itself got merged away; stop scanning its candidates

        db.commit()
        print(f"Done. {merges} duplicate jobs merged.")


if __name__ == "__main__":
    main()
