import json
import logging
from datetime import UTC, datetime

from application_tracker.logging_config import (
    JsonFormatter,
    configure_logging,
)


def test_json_formatter_serializes_structured_fields() -> None:
    record = logging.makeLogRecord(
        {
            "name": "application_tracker.api",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "HTTP request completed",
            "args": (),
            "http_method": "GET",
            "path": "/health",
            "status_code": 200,
            "duration_ms": 12.5,
        }
    )

    output = JsonFormatter().format(record)
    payload = json.loads(output)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "application_tracker.api"
    assert payload["message"] == "HTTP request completed"
    assert payload["http_method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 12.5

    timestamp = datetime.fromisoformat(
        payload["timestamp"]
    )
    assert timestamp.tzinfo is UTC


def test_configure_logging_uses_requested_level() -> None:
    root_logger = logging.getLogger()
    previous_handlers = root_logger.handlers.copy()
    previous_level = root_logger.level

    try:
        configure_logging("DEBUG")

        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 1
        assert isinstance(
            root_logger.handlers[0].formatter,
            JsonFormatter,
        )
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(previous_handlers)
        root_logger.setLevel(previous_level)
