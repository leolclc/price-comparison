import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

# Add collector dir to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_db import get_engine, get_session_factory
from app_models import SearchTerm
from jobs.collector_job import CollectorJob
from sqlalchemy import select, update

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("COLLECTOR_RUN_ONCE")


async def main() -> None:
    logger.info("Iniciando ciclo unico de coleta (GitHub Actions / Scheduled Job)...")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        result = await session.execute(
            select(SearchTerm)
            .where(SearchTerm.active == True)  # noqa: E712
            .order_by(SearchTerm.priority.desc(), SearchTerm.search_count.desc())
        )
        terms = [t.term for t in result.scalars().all()]

        if not terms:
            logger.warning("Nenhum termo de busca ativo encontrado no banco.")
            return

        logger.info(f"Termos a coletar ({len(terms)}): {terms}")
        job = CollectorJob(session)
        await job.run(terms)

        now = datetime.now(timezone.utc)
        await session.execute(
            update(SearchTerm)
            .where(SearchTerm.active == True)  # noqa: E712
            .values(last_searched_at=now)
        )
        await session.commit()
        logger.info("Ciclo de coleta finalizado com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
