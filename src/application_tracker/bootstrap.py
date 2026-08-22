from pathlib import Path

from fastapi import FastAPI

from application_tracker.api import create_app
from application_tracker.sqlite_repository import (
    SQLiteApplicationRepository,
)


def build_app(
    database_path: str | Path,
) -> FastAPI:
    repository = SQLiteApplicationRepository(
        database_path
    )
    return create_app(repository)
