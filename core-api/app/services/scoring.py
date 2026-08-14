"""Soft scoring (FR-402) + deterministic rationale (FR-403).

Only scores jobs that already survived `evaluate_hard_filters()`
(app/services/matching.py) — this module doesn't re-run hard filters.

Of FR-402's five factors, two have real signal from Greenhouse/Lever data
today, one is partial, and two are structural no-ops for the same reason
1.4b's experience-band/ghost-score checks were: the adapters never
populate the structured fields (`job.seniority_band`, `companies
.size_band`/`industry`) spec assumes exist. A factor with no data is
marked `evaluated: False`, not defaulted to a fake neutral value — FR-403
requires the rationale be honest, and a silent default would overstate
its precision.

Final score is a weighted average over *evaluated* factors only,
renormalised by the sum of their weights — so missing factors don't
mechanically deflate every score by the same fixed amount.
"""

import math
from dataclasses import dataclass

from app.models.job import Job
from app.models.user import UserSettings
from app.services.dedup import title_similarity

WEIGHTS = {
    "embedding_similarity": 0.40,
    "title_family_match": 0.25,
    "skill_overlap": 0.20,
    "seniority_alignment": 0.10,
    "company_signal": 0.05,
}


@dataclass
class MatchScoreResult:
    score: float
    factors: dict


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_match_score(
    job: Job,
    candidate_embedding: list[float],
    settings: UserSettings,
    confirmed_skills: list[str],
) -> MatchScoreResult:
    factors: dict[str, dict] = {}

    if job.jd_embedding is not None:
        similarity = _cosine_similarity(candidate_embedding, list(job.jd_embedding))
        factors["embedding_similarity"] = {"evaluated": True, "value": similarity}
    else:
        factors["embedding_similarity"] = {"evaluated": False}

    target_titles = settings.job_preferences.get("target_titles") or []
    if target_titles:
        best = max(title_similarity(job.title, t) for t in target_titles)
        factors["title_family_match"] = {"evaluated": True, "value": best}
    else:
        factors["title_family_match"] = {"evaluated": False}

    if confirmed_skills:
        jd_lower = job.jd_text.lower()
        matched = [s for s in confirmed_skills if s.lower() in jd_lower]
        factors["skill_overlap"] = {
            "evaluated": True,
            "value": len(matched) / len(confirmed_skills),
            "matched_skills": matched,
        }
    else:
        factors["skill_overlap"] = {"evaluated": False}

    # Structural no-ops: adapters never populate these source fields.
    factors["seniority_alignment"] = {"evaluated": False}
    factors["company_signal"] = {"evaluated": False}

    evaluated_weight = sum(
        WEIGHTS[key] for key, f in factors.items() if f["evaluated"]
    )
    if evaluated_weight == 0:
        return MatchScoreResult(score=0.0, factors=factors)

    weighted_sum = sum(
        WEIGHTS[key] * f["value"] for key, f in factors.items() if f["evaluated"]
    )
    score = weighted_sum / evaluated_weight
    return MatchScoreResult(score=score, factors=factors)
