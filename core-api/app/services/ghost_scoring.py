"""Ghost-job scoring (FR-306) — partial implementation.

Spec lists five signals: repost frequency, days since first seen,
presence of a live ATS req ID, whether the company board still lists it,
historical response rate for that company. Only two are honestly
computable right now:

- "Still lists it": approximated via `last_seen_at` staleness relative to
  the most recent successful ingestion pass. worker-ingest does a full
  board sync each run — a job not touched in the latest run has fallen
  off the source (filled/removed), not just gone quiet.
- Age: `first_seen_at` staleness — an evergreen listing open far longer
  than typical is a known ghost-job pattern.

Not implemented: repost frequency (needs repost-event tracking, not just
first/last-seen timestamps), live ATS req ID presence (adapters don't
currently extract this), historical response rate (needs the Feedback
Plane, §3.8, Phase 3). Score is a floor, not a real ghost-job classifier,
until those land.

`latest_ingest_at` is passed in as `max(last_seen_at)` across all jobs
rather than wall-clock now() — ingestion runs sporadically in dev, and
using real now() would mark everything "stale" between manual runs.
"""

from dataclasses import dataclass
from datetime import datetime

from app.models.job import Job

STALE_AFTER_DAYS = 3  # not touched in the last N days of ingestion => delisted
EVERGREEN_AFTER_DAYS = 60  # still listed, but open this long => mild penalty
EVERGREEN_DECAY_RANGE_DAYS = 90
GHOST_FLOOR = 0.4  # evergreen alone shouldn't zero out a job, just derank it


@dataclass
class GhostScoreResult:
    score: float
    reason: str  # "active" | "delisted" | "evergreen"


def compute_ghost_score(job: Job, latest_ingest_at: datetime) -> GhostScoreResult:
    days_since_last_seen = (latest_ingest_at - job.last_seen_at).days
    if days_since_last_seen > STALE_AFTER_DAYS:
        return GhostScoreResult(0.0, "delisted")

    days_open = (latest_ingest_at - job.first_seen_at).days
    if days_open > EVERGREEN_AFTER_DAYS:
        overage = min(days_open - EVERGREEN_AFTER_DAYS, EVERGREEN_DECAY_RANGE_DAYS)
        fraction = overage / EVERGREEN_DECAY_RANGE_DAYS
        score = 1.0 - fraction * (1.0 - GHOST_FLOOR)
        return GhostScoreResult(max(GHOST_FLOOR, score), "evergreen")

    return GhostScoreResult(1.0, "active")
