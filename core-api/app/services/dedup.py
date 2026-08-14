"""Cross-source dedup (FR-305): company + fuzzy title + JD embedding
cosine > 0.92 + location overlap.

Tuned deliberately conservative after a first pass on real data (1223
Greenhouse/Lever postings) produced 230 false-positive merges — companies
like Palantir post near-identical JD templates for genuinely different
reqs (same title across many cities; "Internship" vs "New Grad" variants
of the same template). Two fixes from that failure:

1. Title threshold raised 0.75 -> 0.95. At 0.75, shared boilerplate
   ("Forward Deployed Software Engineer, ___ - Commercial") swamped the
   one differing word that actually mattered.
2. Location check now requires overlap on raw `locations` strings, not
   just `Job.countries` (ISO codes). The countries-only check had a hole:
   it only rejected when *both* sides had resolved countries that didn't
   overlap — an unresolved side (common for cities outside the curated
   10-country list, e.g. most Palantir offices) skipped the check
   entirely, letting same-title-different-city postings through.

True FR-305 duplicates (same req scraped from two ATSs/aggregators) share
near-identical title AND location AND JD text — this is a much narrower
bar than "similar enough," intentionally, since a false-positive merge
silently hides a real distinct job from the candidate.
"""

from difflib import SequenceMatcher

from app.models.job import Job

COSINE_SIMILARITY_THRESHOLD = 0.92
TITLE_SIMILARITY_THRESHOLD = 0.95


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _normalized_locations(job: Job) -> set[str]:
    return {loc.strip().lower() for loc in job.locations if loc.strip()}


def is_likely_duplicate(a: Job, b: Job, cosine_distance: float) -> bool:
    if cosine_distance > (1 - COSINE_SIMILARITY_THRESHOLD):
        return False
    if title_similarity(a.title, b.title) < TITLE_SIMILARITY_THRESHOLD:
        return False
    locs_a, locs_b = _normalized_locations(a), _normalized_locations(b)
    if (locs_a or locs_b) and not locs_a & locs_b:
        return False
    return True
