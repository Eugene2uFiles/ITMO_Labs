from __future__ import annotations

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_NAME = "tea_mixer.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(threadName)s | %(name)s | %(message)s"
_configured = False
_log_path: Path | None = None


def _candidate_log_dirs() -> list[Path]:
    candidates = []
    for env_name in ("FLET_APP_STORAGE_DATA", "FLET_APP_STORAGE_TEMP"):
        value = os.getenv(env_name)
        if value:
            candidates.append(Path(value))
    candidates.extend(
        [
            Path(__file__).parent / "data",
            Path.cwd() / "data",
        ]
    )
    return candidates


def _create_file_handler() -> RotatingFileHandler | None:
    global _log_path
    for directory in _candidate_log_dirs():
        try:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / LOG_NAME
            handler = RotatingFileHandler(
                path,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            _log_path = path
            return handler
        except OSError:
            continue
    return None


def configure_logging() -> logging.Logger:
    global _configured
    root = logging.getLogger()
    if _configured:
        return logging.getLogger("tea_mixer")

    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = _create_file_handler()
    if file_handler is not None:
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    sys.excepthook = _system_exception_hook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_exception_hook

    _configured = True
    logger = logging.getLogger("tea_mixer")
    logger.info(
        "Logging initialized: platform=%s, python=%s, log_file=%s",
        os.getenv("FLET_PLATFORM", "unknown"),
        sys.version.replace("\n", " "),
        _log_path or "unavailable",
    )
    return logger


def _system_exception_hook(exc_type, exc_value, exc_traceback) -> None:
    logging.getLogger("tea_mixer.crash").critical(
        "Unhandled exception",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def _thread_exception_hook(args) -> None:
    logging.getLogger("tea_mixer.crash").critical(
        "Unhandled thread exception: %s",
        args.thread.name if args.thread else "unknown",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def get_log_path() -> Path | None:
    return _log_path

