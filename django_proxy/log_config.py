"""
Loguru setup: console + file sinks, print -> logger.info, Django stdlib log interception.
"""

from __future__ import annotations

import builtins
import inspect
import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger

_configured = False
_original_print = builtins.print


class InterceptHandler(logging.Handler):
    """Route standard logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _print_caller_frame():
    """Frame where print() was invoked (skip print_to_logger / log_config)."""
    frame = inspect.currentframe()
    if frame:
        frame = frame.f_back  # print_to_logger
    log_config = Path(__file__).resolve()
    while frame:
        try:
            path = Path(frame.f_code.co_filename).resolve()
        except (OSError, TypeError, ValueError):
            break
        if path == log_config:
            frame = frame.f_back
            continue
        return frame
        frame = frame.f_back
    return None


def _patch_print_record(record: dict, caller: inspect.FrameType) -> dict:
    file_path = caller.f_code.co_filename
    record["file"].name = Path(file_path).name
    record["file"].path = file_path
    record["line"] = caller.f_lineno
    record["function"] = caller.f_code.co_name
    record["name"] = Path(file_path).name
    return record


def _patch_print() -> None:
    def print_to_logger(*args: Any, **kwargs: Any) -> None:
        target = kwargs.get("file")
        if target is not None and target not in (sys.stdout, sys.stderr):
            _original_print(*args, **kwargs)
            return

        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        message = sep.join(str(arg) for arg in args)
        if end and end != "\n":
            message = f"{message}{end}".rstrip("\n")
        if not message:
            return

        caller = _print_caller_frame()
        if caller is None:
            logger.opt(colors=True).info("<green>{}</green>", message)
            return

        logger.patch(
            lambda record: _patch_print_record(record, caller)
        ).opt(colors=True).info("<green>{}</green>", message)

    builtins.print = print_to_logger


def configure_loguru(
    *,
    base_dir: Path,
    log_level: str = "INFO",
    retention_days: int = 7,
    enable_file: bool = True,
    patch_print: bool = True,
) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level.upper(),
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    if enable_file:
        logger.add(
            log_dir / "proxy_{time:YYYY-MM-DD}.log",
            level=log_level.upper(),
            rotation="00:00",
            retention=f"{retention_days} days",
            compression="zip",
            encoding="utf-8",
            enqueue=True,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            ),
        )

    if patch_print:
        _patch_print()

    logging.captureWarnings(True)
    logger.info("Loguru configured (level={}, file={})", log_level.upper(), enable_file)


def get_logging_config(log_level: str = "INFO") -> dict[str, Any]:
    """Django LOGGING dict — all handlers delegate to loguru."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "loguru": {
                "()": "django_proxy.log_config.InterceptHandler",
            },
        },
        "root": {
            "handlers": ["loguru"],
            "level": log_level.upper(),
        },
        "loggers": {
            "django": {
                "handlers": ["loguru"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "django.server": {
                "handlers": ["loguru"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "django.request": {
                "handlers": ["loguru"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "daphne": {
                "handlers": ["loguru"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "channels": {
                "handlers": ["loguru"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "gateway": {
                "handlers": ["loguru"],
                "level": "DEBUG",
                "propagate": False,
            },
            "httpx": {
                "handlers": ["loguru"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }


__all__ = ["logger", "InterceptHandler", "configure_loguru", "get_logging_config"]
