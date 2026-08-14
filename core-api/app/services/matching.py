"""Hard filters (FR-401) — cheap, deterministic, evaluated before scoring.

Each job gets attributed to exactly one exclusion reason (first filter it
fails, in the order below) so the Opportunity Report funnel (§6.4) can show
mutually-exclusive buckets like "187 excluded: experience band mismatch."

Two filters are structurally present but currently no-ops on real data:
- experience_band: Greenhouse/Lever adapters never populate `jobs.exp_min`/
  `exp_max` (their public APIs don't return structured ranges), so every
  job passes this check until that's sourced from JD text or elsewhere.
- ghost_score: ghost-job scoring (FR-306) isn't implemented yet — `jobs
  .ghost_score` is always NULL, so every job passes this check too.

Two filters from FR-401 are NOT implemented here yet: already-applied
dedup and per-company cooldown both need the `applications` table, which
doesn't exist until Phase 1.6 (execution/state machine).
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.job import Company, Job
from app.models.user import UserSettings

GHOST_SCORE_THRESHOLD = 0.3

REASON_LABELS = {
    "experience_band_mismatch": "experience band mismatch",
    "ctc_below_floor": "below your CTC floor",
    "country_incompatible": "location incompatible",
    "work_authorization_incompatible": "work authorization incompatible",
    "company_blocklisted": "company blocklist",
    "ghost_score_below_threshold": "likely reposted/stale",
}


@dataclass
class HardFilterResult:
    passed: bool
    reason: str | None  # key into REASON_LABELS, None when passed


def evaluate_hard_filters(
    job: Job, company_name: str, settings: UserSettings, answers: dict[str, str]
) -> HardFilterResult:
    prefs = settings.job_preferences

    years = _parse_float(answers.get("total_experience_years"))
    if years is not None and (job.exp_min is not None or job.exp_max is not None):
        lo = job.exp_min if job.exp_min is not None else 0.0
        hi = job.exp_max if job.exp_max is not None else float("inf")
        if not (lo <= years <= hi):
            return HardFilterResult(False, "experience_band_mismatch")

    ctc_min = prefs.get("ctc_min")
    if ctc_min is not None and job.ctc_max is not None and job.ctc_max < ctc_min:
        return HardFilterResult(False, "ctc_below_floor")

    target_countries = set(prefs.get("target_countries") or [])
    if job.countries and target_countries and not (set(job.countries) & target_countries):
        return HardFilterResult(False, "country_incompatible")

    work_auth_raw = answers.get("work_authorized_countries")
    if work_auth_raw:
        authorized = {c.strip() for c in work_auth_raw.split(",") if c.strip()}
        if job.countries and authorized and not (set(job.countries) & authorized):
            return HardFilterResult(False, "work_authorization_incompatible")

    blocklist = {c.lower() for c in (prefs.get("blocklist_companies") or [])}
    if blocklist and company_name.lower() in blocklist:
        return HardFilterResult(False, "company_blocklisted")

    if job.ghost_score is not None and job.ghost_score < GHOST_SCORE_THRESHOLD:
        return HardFilterResult(False, "ghost_score_below_threshold")

    return HardFilterResult(True, None)


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


@dataclass
class HardFilterFunnel:
    scanned: int
    passed: int
    excluded_by_reason: dict[str, int]


def run_hard_filter_funnel(
    db: Session, settings: UserSettings, answers: dict[str, str]
) -> HardFilterFunnel:
    """Shared by /matches/summary (1.4b) and /matches/opportunity-report (1.5)."""
    excluded_by_reason: dict[str, int] = dict.fromkeys(REASON_LABELS, 0)
    passed = 0
    scanned = 0

    rows = db.query(Job, Company.canonical_name).join(Company, Company.id == Job.company_id)
    for job, company_name in rows:
        scanned += 1
        result = evaluate_hard_filters(job, company_name, settings, answers)
        if result.passed:
            passed += 1
        else:
            excluded_by_reason[result.reason] += 1

    return HardFilterFunnel(scanned=scanned, passed=passed, excluded_by_reason=excluded_by_reason)
