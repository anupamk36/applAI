import re
from datetime import datetime

import httpx

from ingest.adapters.base import RawJobPosting, SourceAdapter

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


class GreenhouseAdapter(SourceAdapter):
    source_name = "greenhouse"

    def __init__(self, board_token: str, company_name: str):
        self.board_token = board_token
        self.company_name = company_name

    def fetch(self) -> list[RawJobPosting]:
        resp = httpx.get(
            GREENHOUSE_API.format(board=self.board_token),
            params={"content": "true"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        postings = []
        for job in data.get("jobs", []):
            location = (job.get("location") or {}).get("name")
            postings.append(
                RawJobPosting(
                    source=self.source_name,
                    source_job_id=str(job["id"]),
                    source_url=job.get("absolute_url", ""),
                    company_name=self.company_name,
                    title=job.get("title", ""),
                    jd_text=_strip_html(job.get("content", "")),
                    apply_url=job.get("absolute_url", ""),
                    ats="greenhouse",
                    locations=[location] if location else [],
                    posted_at=_parse_dt(job.get("updated_at")),
                )
            )
        return postings


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
