import asyncio
import logging
import os
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app_db import get_engine, get_session_factory
from app_models import SearchTerm
from jobs.collector_job import CollectorJob

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("COLLECTOR_MAIN")

COLLECTOR_INTERVAL_MINUTES = int(
    os.environ.get("COLLECTOR_INTERVAL_MINUTES", "60")
)


async def run_collection(session_factory) -> None:
    async with session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(SearchTerm)
            .where(SearchTerm.active == True)  # noqa: E712
            .order_by(SearchTerm.priority.desc(), SearchTerm.search_count.desc())
        )
        terms = [t.term for t in result.scalars().all()]

        if not terms:
            logger.warning("No active search terms found")
            return

        logger.info(f"Running collection for {len(terms)} terms: {terms}")
        job = CollectorJob(session)
        await job.run(terms)

        from datetime import datetime, timezone, timedelta
        from sqlalchemy import update
        now = datetime.now(timezone.utc)
        next_run = now + timedelta(minutes=COLLECTOR_INTERVAL_MINUTES)
        await session.execute(
            update(SearchTerm)
            .where(SearchTerm.active == True)  # noqa: E712
            .values(last_searched_at=now, next_search_at=next_run)
        )
        await session.commit()
        logger.info("Collection cycle complete")


async def main() -> None:
    logger.info("FarmaCompare Collector starting...")

    await asyncio.sleep(5)

    engine = get_engine()
    session_factory = get_session_factory(engine)

    try:
        await run_collection(session_factory)
    except Exception as e:
        logger.error(f"Error during initial collection: {e}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_collection,
        "interval",
        minutes=COLLECTOR_INTERVAL_MINUTES,
        args=[session_factory],
        id="collection_job",
    )
    scheduler.start()
    logger.info(
        f"Scheduler started. Next run in {COLLECTOR_INTERVAL_MINUTES} minutes."
    )

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Collector stopped")


if __name__ == "__main__":
    asyncio.run(main())
