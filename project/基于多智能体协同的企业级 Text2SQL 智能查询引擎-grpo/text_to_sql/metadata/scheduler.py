"""
Metadata collection scheduler.
"""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler


logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def create_schema_collection_job(refresh_callback, cron_hour: int = 2, cron_minute: int = 0):
    """Create the daily metadata and retrieval-index refresh job."""

    async def daily_schema_collection():
        logger.info("Starting daily schema collection at %s", datetime.now())
        try:
            await asyncio.to_thread(refresh_callback)
            logger.info("Schema collection completed at %s", datetime.now())
        except Exception:
            logger.exception("Schema collection failed")
            raise

    scheduler.add_job(
        daily_schema_collection,
        "cron",
        hour=cron_hour,
        minute=cron_minute,
        id="text2sql-schema-refresh",
        replace_existing=True,
    )
    return daily_schema_collection


def start_scheduler(refresh_callback):
    create_schema_collection_job(refresh_callback)
    if not scheduler.running:
        scheduler.start()
    logger.info("Metadata scheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Metadata scheduler stopped")
