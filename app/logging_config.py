import logging
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import Request

LOG_DIR = Path("logs")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Call once, before the FastAPI app is created."""
    LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger()
    if root.handlers:  # avoid duplicate handlers on uvicorn --reload
        return
    root.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_DIR / "thinksync.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)

    # Quiet noisy libraries
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.ERROR)


logger = logging.getLogger("thinksync.http")


async def log_requests(request: Request, call_next):
    """HTTP middleware: request id, timing, one log line per request."""
    request_id = uuid.uuid4().hex[:8]
    request.state.request_id = request_id
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception(
            "[%s] %s %s -> unhandled error (%.1f ms)",
            request_id, request.method, request.url.path, elapsed,
        )
        raise

    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "[%s] %s %s -> %d (%.1f ms)",
        request_id, request.method, request.url.path, response.status_code, elapsed,
    )
    response.headers["X-Request-ID"] = request_id
    return response