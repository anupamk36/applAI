from datetime import datetime, timezone

import httpx

from ingest.adapters.base import RawJobPosting, SourceAdapter

LEVER_API = "https://api.lever.co/v0/postings/{account}"


class LeverAdapter(SourceAdapter):
    source_name = "lever"

    def __init__(self, account: str, company_name: str):
        self.account = account
        self.company_name = company_name

    def fetch(self) -> list[RawJobPosting]:
        resp = httpx.get(
            LEVER_API.format(account=self.account),
            params={"mode": "json"},
            timeout=30,
        )
        resp.raise_for_status()
        jobs = resp.json()

        postings = []
        for job in jobs:
            categories = job.get("categories") or {}
            all_locations = categories.get("allLocations") or (
                [categories["location"]] if categories.get("location") else []
            )
            postings.append(
                RawJobPosting(
                    source=self.source_name,
                    source_job_id=str(job["id"]),
                    source_url=job.get("hostedUrl", ""),
                    company_name=self.company_name,
                    title=job.get("text", ""),
                    jd_text=job.get("descriptionPlain", "") or "",
                    apply_url=job.get("applyUrl") or job.get("hostedUrl", ""),
                    ats="lever",
                    locations=all_locations,
                    remote_policy=categories.get("workplaceType"),
                    posted_at=_parse_created_at(job.get("createdAt")),
                )
            )
        return postings


def _parse_created_at(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
