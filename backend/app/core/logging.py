"""Structured logging. Never log passwords, API secrets, TOTP, or access tokens."""

import logging
import sys

REDACT_KEYS = frozenset(
    {
        "password",
        "confirm_password",
        "api_secret",
        "api_key",
        "totp",
        "access_token",
        "refresh_token",
        "jwt_secret",
        "encryption_key",
    }
)


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s request_id=%(request_id)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True
