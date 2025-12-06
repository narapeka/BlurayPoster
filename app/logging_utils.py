import logging
import os
import threading
from collections import deque
from logging.handlers import TimedRotatingFileHandler
from typing import Deque, Dict, List, Optional


class LogBuffer:
    """
    Thread-safe fixed-size log buffer for live log viewing.
    Stores structured entries for easy JSON serialization.
    """

    def __init__(self, max_entries: int = 200):
        self._buffer: Deque[Dict[str, str]] = deque(maxlen=max_entries)
        self._lock = threading.Lock()

    def add(self, level: str, message: str, created: float, name: str) -> None:
        entry = {
            "level": level,
            "message": message,
            "created": created,
            "logger": name,
        }
        with self._lock:
            self._buffer.append(entry)

    def get_entries(self) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._buffer)


class InMemoryLogHandler(logging.Handler):
    """
    Logging handler that pushes records into LogBuffer.
    """

    def __init__(self, buffer: LogBuffer):
        super().__init__()
        self._buffer = buffer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._buffer.add(record.levelname, msg, record.created, record.name)
        except Exception:
            self.handleError(record)


def setup_logging(log_level_str: str, log_buffer: Optional[LogBuffer] = None) -> None:
    """
    Configure root logger with console, rotating file, and optional in-memory buffer.
    """
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)

    logger = logging.getLogger()
    log_level = getattr(logging, log_level_str.upper(), logging.DEBUG)
    logger.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Avoid duplicate handlers when reloading
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        file_handler = TimedRotatingFileHandler(
            os.path.join(log_directory, "blurayposter.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if log_buffer is not None and not any(
        isinstance(h, InMemoryLogHandler) for h in logger.handlers
    ):
        buffer_handler = InMemoryLogHandler(log_buffer)
        buffer_handler.setLevel(log_level)
        buffer_handler.setFormatter(formatter)
        logger.addHandler(buffer_handler)


