"""Heuristic location-string -> ISO country code tagging.

Same "ship a rule-based version now, swap for a real service later" approach
as the Phase 0 resume parser (core-api/app/services/resume_parser.py):
keyword/city matching against free-text ATS location strings. Imperfect on
ambiguous or unlisted locations (see plan's deferred-decisions note) —
acceptable for v1, where this only drives a preference filter.
"""

import re

# code -> patterns (country names, common abbreviations, major cities/states).
# Ordered roughly by expected posting volume for this ICP.
COUNTRY_PATTERNS: dict[str, list[str]] = {
    "IN": [
        "india", "bengaluru", "bangalore", "mumbai", "delhi", "ncr",
        "gurgaon", "gurugram", "hyderabad", "pune", "chennai", "noida",
        "kolkata", "ahmedabad",
    ],
    "US": [
        "united states", "usa", "u.s.", "us", "san francisco", "sf",
        "new york", "nyc", "seattle", "sea", "chicago", "chi", "austin",
        "boston", "los angeles", "la", "denver", "atlanta",
    ],
    "GB": ["united kingdom", "uk", "london", "manchester", "edinburgh"],
    "CA": ["canada", "toronto", "vancouver", "montreal"],
    "AU": ["australia", "sydney", "melbourne"],
    "DE": ["germany", "berlin", "munich"],
    "NL": ["netherlands", "amsterdam"],
    "SG": ["singapore"],
    "AE": ["united arab emirates", "uae", "dubai", "abu dhabi"],
    "SE": ["sweden", "stockholm"],
}

_COMPILED = {
    code: [re.compile(rf"\b{re.escape(p)}\b", re.IGNORECASE) for p in patterns]
    for code, patterns in COUNTRY_PATTERNS.items()
}


def infer_countries(locations: list[str]) -> list[str]:
    """Returns sorted ISO country codes matched across all location strings.

    Empty list means unresolved (e.g. remote postings with no location text)
    — callers should treat that as "no country restriction", not exclude it.
    """
    joined = " | ".join(locations)
    matched = {
        code for code, patterns in _COMPILED.items() if any(p.search(joined) for p in patterns)
    }
    return sorted(matched)
