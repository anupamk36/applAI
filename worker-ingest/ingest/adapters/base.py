from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawJobPosting:
    """Common shape every source adapter normalises into (FR-301)."""

    source: str
    source_job_id: str
    source_url: str
    company_name: str
    title: str
    jd_text: str
    apply_url: str
    ats: str | None = None
    locations: list[str] = field(default_factory=list)
    remote_policy: str | None = None
    posted_at: datetime | None = None


class SourceAdapter(ABC):
    source_name: str

    @abstractmethod
    def fetch(self) -> list[RawJobPosting]:
        """Fetch and return raw postings from this source."""
