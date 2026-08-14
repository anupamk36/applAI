"""Server-side registry of known Answer Bank semantic keys (FR-201).

Only the client-writable *value* comes from the request — sensitivity and
default policy are decided here, not by the client, matching FR-202
("sensitive keys ... default ask-me"). Minimal slice for now: just what
Phase 1.4's hard filters need. Full India Answer Bank (§3.2) grows this
registry in Phase 1.6.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class KeySpec:
    label: str
    value_type: str  # "number" | "country_list"
    is_sensitive: bool = False


SEMANTIC_KEY_REGISTRY: dict[str, KeySpec] = {
    "total_experience_years": KeySpec(
        label="Total years of experience", value_type="number"
    ),
    "work_authorized_countries": KeySpec(
        label="Countries you can work in without sponsorship", value_type="country_list"
    ),
}


def default_policy(is_sensitive: bool) -> str:
    return "ask_me" if is_sensitive else "auto_fill"
