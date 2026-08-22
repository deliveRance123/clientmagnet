import logging
import sys

from app.core.config import settings

# Configure logging formats
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    """Sets up global application logging."""
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress verbose standard library/third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("app")
    logger.info(f"Logging initialized with level: {logging.getLevelName(log_level)}")
