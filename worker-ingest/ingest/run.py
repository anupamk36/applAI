"""Phase 0 manual trigger: `uv run python -m ingest.run`.

Runs Greenhouse + Lever adapters for the seed boards/accounts in config.py
and upserts results into the shared Postgres `jobs`/`companies`/`job_sources`
tables. A scheduled/queued version (Celery/ARQ per spec §2.2) is Phase 1+.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ingest.adapters.base import SourceAdapter
from ingest.adapters.greenhouse import GreenhouseAdapter
from ingest.adapters.lever import LeverAdapter
from ingest.config import settings
from ingest.persist import upsert_posting


def build_adapters() -> list[SourceAdapter]:
    adapters: list[SourceAdapter] = []
    for token, name in settings.greenhouse_boards.items():
        adapters.append(GreenhouseAdapter(board_token=token, company_name=name))
    for account, name in settings.lever_accounts.items():
        adapters.append(LeverAdapter(account=account, company_name=name))
    return adapters


def main():
    engine = create_engine(settings.database_url)
    total_created = 0
    total_updated = 0

    with Session(engine) as db:
        for adapter in build_adapters():
            try:
                postings = adapter.fetch()
            except Exception as e:
                print(f"[{adapter.source_name}] fetch failed: {e}")
                continue

            created = updated = 0
            for posting in postings:
                _, was_created = upsert_posting(db, posting)
                created += was_created
                updated += not was_created
            db.commit()

            total_created += created
            total_updated += updated
            print(f"[{adapter.source_name}] {len(postings)} postings -> {created} new, {updated} updated")

    print(f"Done. {total_created} new jobs, {total_updated} updated.")


if __name__ == "__main__":
    main()
