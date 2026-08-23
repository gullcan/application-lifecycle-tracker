import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self


DEFAULT_DATABASE_PATH = "application_tracker.db"
DEFAULT_LOG_LEVEL = "INFO"

SUPPORTED_LOG_LEVELS: frozenset[str] = frozenset(
    {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }
)


@dataclass(frozen=True)
class Settings:
    database_path: Path
    log_level: str

    @classmethod
    def from_environment(cls) -> Self:
        database_path_value = os.getenv(
            "APPLICATION_TRACKER_DATABASE_PATH",
            DEFAULT_DATABASE_PATH,
        ).strip()

        if not database_path_value:
            raise ValueError(
                "database path cannot be blank"
            )

        log_level = os.getenv(
            "APPLICATION_TRACKER_LOG_LEVEL",
            DEFAULT_LOG_LEVEL,
        ).strip().upper()

        if log_level not in SUPPORTED_LOG_LEVELS:
            raise ValueError(
                f"unsupported log level: '{log_level}'"
            )

        return cls(
            database_path=Path(database_path_value),
            log_level=log_level,
        )
