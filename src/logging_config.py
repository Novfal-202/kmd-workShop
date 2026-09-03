"""Structured logging configuration for claim evaluations and review decisions.

Kept separate from src/services/policy_engine/ (which stays pure/import-free per
constitution Article III.1); callers in src/api/ import and use this logger.
"""

import json
import logging
import sys

logger = logging.getLogger("expense_policy_engine")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "event": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "extra_fields"):
            payload.update(record.extra_fields)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False


def log_event(event: str, **fields) -> None:
    logger.info(event, extra={"extra_fields": fields})
