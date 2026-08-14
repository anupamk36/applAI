from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.job import Company, Job
from app.models.user import User
from app.schemas.job import JobListOut, JobOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListOut)
def list_jobs(
    limit: int = 25,
    offset: int = 0,
    title: str | None = None,
    company: str | None = None,
    location: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filters = []
    if title:
        filters.append(Job.title.ilike(f"%{title}%"))
    if company:
        filters.append(Company.canonical_name.ilike(f"%{company}%"))
    if location:
        filters.append(func.array_to_string(Job.locations, ",").ilike(f"%{location}%"))

    count_stmt = select(func.count(Job.id)).join(Company, Company.id == Job.company_id)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = db.execute(count_stmt).scalar()

    # Round-robin across companies rather than a straight recency sort: a
    # single re-ingest run touches one company's rows last (whichever
    # source adapter runs last), which otherwise floods the default page
    # with just that company. Ranked-within-company, then interleaved.
    rank = (
        func.row_number()
        .over(partition_by=Job.company_id, order_by=Job.first_seen_at.desc())
        .label("rank")
    )
    ranked_query = select(Job, Company.canonical_name.label("company_name"), rank).join(
        Company, Company.id == Job.company_id
    )
    if filters:
        ranked_query = ranked_query.where(*filters)
    ranked = ranked_query.subquery()
    job_columns = [c for c in ranked.c if c.name != "rank"]

    stmt = (
        select(*job_columns)
        .order_by(ranked.c.rank, ranked.c.first_seen_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    items = [JobOut(**row._mapping) for row in rows]
    return JobListOut(items=items, total=total, limit=limit, offset=offset)
