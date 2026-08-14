"""Phase 1.3 manual trigger: `uv run python -m app.scripts.embed_jobs`.

Backfills `jobs.jd_embedding` for any row where it's still NULL — new rows
land NULL from worker-ingest (a separate process/venv that doesn't call
Voyage), this script is what actually embeds them. A queued/scheduled
version (Celery/ARQ) is future work once ingestion runs on a schedule.

Batch size, inter-batch sleep, and per-JD truncation are sized for
Voyage's unfunded-account throttle (3 req/min, 10K tokens/min) — see
plan's Phase 1.3 deferred decision. Real job postings run up to ~24K
chars (~6K tokens); untruncated batches of 8 land at or over the 10K TPM
cap on their own, so retries on those batches fail identically every
time — this isn't a transient-error problem, it's a request-sizing one.
Safe to raise MAX_JD_CHARS/BATCH_SIZE and shrink SLEEP_SECONDS once a
payment method is added.
"""

import time

from voyageai.error import RateLimitError

from app.db import SessionLocal
from app.models.job import Job
from app.services.embeddings import embed_documents

BATCH_SIZE = 8
SLEEP_SECONDS = 21  # keeps us under 3 req/min with margin
MAX_JD_CHARS = 2000  # ~500 tokens; keeps an 8-job batch well under 10K TPM


def embed_with_backoff(texts: list[str]) -> list[list[float]]:
    delay = SLEEP_SECONDS
    for attempt in range(6):
        try:
            return embed_documents(texts)
        except RateLimitError:
            print(f"  rate limited, backing off {delay}s (attempt {attempt + 1})")
            time.sleep(delay)
            delay *= 1.5
    raise RuntimeError("Voyage rate limit: exhausted retries")


def main():
    with SessionLocal() as db:
        total = 0
        while True:
            jobs = (
                db.query(Job)
                .filter(Job.jd_embedding.is_(None))
                .limit(BATCH_SIZE)
                .all()
            )
            if not jobs:
                break

            texts = [f"{job.title}\n\n{job.jd_text[:MAX_JD_CHARS]}" for job in jobs]
            embeddings = embed_with_backoff(texts)

            for job, embedding in zip(jobs, embeddings):
                job.jd_embedding = embedding

            db.commit()
            total += len(jobs)
            print(f"Embedded {total} jobs so far...")
            time.sleep(SLEEP_SECONDS)

        print(f"Done. {total} jobs embedded.")


if __name__ == "__main__":
    main()
