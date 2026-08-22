import asyncio
import logging
from app.core.logging import setup_logging
from app.db.session import SessionLocal
from app.services.background_worker import BackgroundWorker

logger = logging.getLogger("app.worker")


async def main():
    setup_logging()
    logger.info("Initializing standalone Client Magnet background worker...")
    worker = BackgroundWorker(session_factory=SessionLocal, poll_interval_seconds=60)
    await worker.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Shutting down background worker...")
        await worker.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
