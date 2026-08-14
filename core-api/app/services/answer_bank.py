"""Server-side registry of known Answer Bank semantic keys (FR-201).

Only the client-writable *value* comes from the request — sensitivity and
default policy are decided here, not by the client, matching FR-202
("sensitive keys ... default ask-me"). Grown incrementally by what each
phase actually needs to exercise, not the full spec §3.2 India Answer Bank
up front:
- Phase 1.4: total_experience_years, work_authorized_countries (hard filters).
- Phase 1.6d: linkedin_url, personal_website — added because these are two
  of the five real custom questions found on a live Greenhouse page
  (Discord) during 1.6's adapter research, giving Tier 3 semantic matching
  concrete real targets instead of an empty catalog.
- Phase 1.6d: disability_status — added so FR-603's "sensitive fields
  always escalate" is actually exercisable against real data (Discord's
  page has a real Disability Status question), not a dead code path.
- Phase 1.6f: first_name, last_name, phone, current_country,
  current_location — spec §3.2's "Identity & eligibility" fields. Found
  missing while wiring apply-runner: the Greenhouse adapter's Tier 1
  fields map straight to these semantic keys via selector (no Tier 3
  needed for them — Tier 1 catches them first), but nothing anywhere in
  the data model held an actual *value* for a candidate's name or phone
  number until now. Can't fill a real form field without one.

`canonical_question` is what Tier 3 embeds and compares DOM field labels
against — deliberately phrased like a question, not a form-field label,
since that's what a JD/form label most resembles semantically.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class KeySpec:
    label: str
    value_type: str  # "number" | "country_list" | "text"
    canonical_question: str
    is_sensitive: bool = False


SEMANTIC_KEY_REGISTRY: dict[str, KeySpec] = {
    "total_experience_years": KeySpec(
        label="Total years of experience",
        value_type="number",
        canonical_question="How many years of professional experience do you have?",
    ),
    "work_authorized_countries": KeySpec(
        label="Countries you can work in without sponsorship",
        value_type="country_list",
        canonical_question=(
            "Are you legally authorized to work in this country without visa sponsorship?"
        ),
    ),
    "linkedin_url": KeySpec(
        label="LinkedIn profile URL",
        value_type="text",
        canonical_question="What is your LinkedIn profile URL?",
    ),
    "personal_website": KeySpec(
        label="Personal website or portfolio URL",
        value_type="text",
        canonical_question="What is your personal website or portfolio URL?",
    ),
    "disability_status": KeySpec(
        label="Disability status",
        value_type="text",
        canonical_question="Do you have a disability?",
        is_sensitive=True,
    ),
    "first_name": KeySpec(
        label="First name", value_type="text", canonical_question="What is your first name?"
    ),
    "last_name": KeySpec(
        label="Last name", value_type="text", canonical_question="What is your last name?"
    ),
    "phone": KeySpec(
        label="Phone number", value_type="text", canonical_question="What is your phone number?"
    ),
    "country": KeySpec(
        label="Country of residence",
        value_type="text",
        canonical_question="What country do you currently live in?",
    ),
    "current_location": KeySpec(
        label="Current city",
        value_type="text",
        canonical_question="What city do you currently live in?",
    ),
}


def default_policy(is_sensitive: bool) -> str:
    return "ask_me" if is_sensitive else "auto_fill"
