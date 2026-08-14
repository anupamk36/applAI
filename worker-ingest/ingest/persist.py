from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ingest.adapters.base import RawJobPosting
from ingest.geo import infer_countries
from ingest.models import Company, Job, JobSource


def get_or_create_company(db: Session, name: str) -> Company:
    company = db.query(Company).filter(Company.canonical_name == name).first()
    if company:
        return company
    company = Company(canonical_name=name)
    db.add(company)
    db.flush()
    return company


def upsert_posting(db: Session, posting: RawJobPosting) -> tuple[Job, bool]:
    """Idempotent per (source, source_job_id). Returns (job, created)."""
    now = datetime.now(timezone.utc)

    existing_source = (
        db.query(JobSource)
        .filter(JobSource.source == posting.source, JobSource.source_job_id == posting.source_job_id)
        .first()
    )
    countries = infer_countries(posting.locations)

    if existing_source:
        job = db.get(Job, existing_source.job_id)
        job.title = posting.title
        job.jd_text = posting.jd_text
        job.locations = posting.locations
        job.countries = countries
        job.remote_policy = posting.remote_policy
        job.apply_url = posting.apply_url
        job.last_seen_at = now
        existing_source.seen_at = now
        return job, False

    company = get_or_create_company(db, posting.company_name)
    job = Job(
        company_id=company.id,
        title=posting.title,
        jd_text=posting.jd_text,
        locations=posting.locations,
        countries=countries,
        remote_policy=posting.remote_policy,
        ats=posting.ats,
        apply_url=posting.apply_url,
        first_seen_at=posting.posted_at or now,
        last_seen_at=now,
    )
    db.add(job)
    db.flush()

    db.add(
        JobSource(
            job_id=job.id,
            source=posting.source,
            source_job_id=posting.source_job_id,
            source_url=posting.source_url,
            seen_at=now,
        )
    )
    return job, True
