"""Structured JSON logging via structlog. Never logs secrets/full documents."""

from __future__ import annotations

import logging

import structlog

_REDACT_KEYS = {"password", "hashed_password", "authorization", "jwt", "token", "api_key", "groq_api_key"}


def _redact_processor(_, __, event_dict: dict) -> dict:
    for key in list(event_dict.keys()):
        if key.lower() in _REDACT_KEYS:
            event_dict[key] = "***REDACTED***"
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(level=log_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


def get_logger(*args, **kwargs):
    return structlog.get_logger(*args, **kwargs)
