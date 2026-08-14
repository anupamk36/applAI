"""Heuristic resume parser for Phase 0.

Splits resume text into sections by common headers and emits candidate
FactBase rows for user confirmation. Deliberately rule-based, not an LLM
call — the spec (§7.1) routes resume parsing to a small/fast model, but
Phase 0's job is proving the upload -> parse -> confirm -> fact_base loop,
not extraction quality. Swap the body of `parse_resume` for a model call
in Phase 1 without touching callers.
"""

import io
import re

import docx
from pypdf import PdfReader

SECTION_HEADERS = {
    "employment": ["experience", "employment", "work history"],
    "education": ["education", "academic"],
    "skill": ["skills", "technical skills"],
    "project": ["projects"],
    "certification": ["certifications", "certificates", "licenses"],
}


def extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if filename.lower().endswith(".docx"):
        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs)
    raise ValueError(f"Unsupported file type: {filename}")


def _section_for_line(line: str) -> str | None:
    lowered = line.strip().lower().rstrip(":")
    for kind, headers in SECTION_HEADERS.items():
        if lowered in headers:
            return kind
    return None


def parse_resume(text: str) -> list[dict]:
    """Returns a list of candidate facts: [{kind, payload}, ...]."""
    lines = [line for line in text.splitlines() if line.strip()]

    facts: list[dict] = []
    current_kind: str | None = None
    buffer: list[str] = []

    def flush():
        if current_kind and buffer:
            block = "\n".join(buffer).strip()
            if current_kind == "skill":
                for skill in re.split(r"[,•|]", block):
                    skill = skill.strip()
                    if skill:
                        facts.append({"kind": "skill", "payload": {"name": skill, "raw_text": skill}})
            else:
                facts.append({"kind": current_kind, "payload": {"raw_text": block}})

    for line in lines:
        section = _section_for_line(line)
        if section:
            flush()
            current_kind = section
            buffer = []
            continue
        if current_kind:
            buffer.append(line)

    flush()
    return facts
