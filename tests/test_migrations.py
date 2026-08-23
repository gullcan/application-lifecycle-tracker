import sqlite3
from pathlib import Path

import pytest

from application_tracker.migrations import (
    CURRENT_SCHEMA_VERSION,
    UnsupportedSchemaVersionError,
    migrate_database,
)


def test_migration_creates_current_schema(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    connection = sqlite3.connect(database_path)

    try:
        migrate_database(connection)

        schema_version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]

        table_names = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }
    finally:
        connection.close()

    assert schema_version == CURRENT_SCHEMA_VERSION
    assert "applications" in table_names
    assert "application_status_changes" in table_names


def test_migration_preserves_legacy_application_data(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    connection = sqlite3.connect(database_path)

    try:
        connection.execute(
            """
            CREATE TABLE applications (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                follow_up_at TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO applications (
                id,
                company_name,
                job_title,
                status,
                created_at,
                follow_up_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-application-id",
                "OpenAI",
                "Backend Engineer",
                "applied",
                "2026-08-23T09:00:00+00:00",
                None,
            ),
        )
        connection.commit()

        migrate_database(connection)

        stored_company = connection.execute(
            """
            SELECT company_name
            FROM applications
            WHERE id = ?
            """,
            ("legacy-application-id",),
        ).fetchone()[0]

        schema_version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]
    finally:
        connection.close()

    assert stored_company == "OpenAI"
    assert schema_version == CURRENT_SCHEMA_VERSION


def test_migration_rejects_newer_database_version(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    connection = sqlite3.connect(database_path)

    try:
        newer_version = CURRENT_SCHEMA_VERSION + 1
        connection.execute(
            f"PRAGMA user_version = {newer_version}"
        )

        with pytest.raises(
            UnsupportedSchemaVersionError,
            match="newer than supported",
        ):
            migrate_database(connection)
    finally:
        connection.close()
