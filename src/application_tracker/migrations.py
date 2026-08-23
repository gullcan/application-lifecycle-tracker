import sqlite3
from collections.abc import Callable


CURRENT_SCHEMA_VERSION = 2


class UnsupportedSchemaVersionError(RuntimeError):
    """Raised when a database is newer than the application."""


Migration = Callable[[sqlite3.Connection], None]


def _create_initial_schema(
        connection: sqlite3.Connection,
) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
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
        CREATE TABLE IF NOT EXISTS application_status_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            sequence_number INTEGER NOT NULL,
            previous_status TEXT NOT NULL,
            new_status TEXT NOT NULL,
            changed_at TEXT NOT NULL,
            UNIQUE(application_id, sequence_number),
            FOREIGN KEY (application_id)
                REFERENCES applications(id)
                ON DELETE CASCADE
        )
        """
    )


def _add_personal_productivity_fields(
        connection: sqlite3.Connection,
) -> None:
    connection.execute(
        "ALTER TABLE applications ADD COLUMN source TEXT"
    )
    connection.execute(
        "ALTER TABLE applications ADD COLUMN job_url TEXT"
    )
    connection.execute(
        """
        ALTER TABLE applications
        ADD COLUMN notes TEXT NOT NULL DEFAULT ''
        """
    )
    connection.execute(
        "ALTER TABLE applications ADD COLUMN archived_at TEXT"
    )

MIGRATIONS: dict[int, Migration] = {
    1: _create_initial_schema,
    2: _add_personal_productivity_fields,
}


def _read_schema_version(
        connection: sqlite3.Connection,
) -> int:
    row = connection.execute(
        "PRAGMA user_version"
    ).fetchone()

    return int(row[0])


def migrate_database(
        connection: sqlite3.Connection,
) -> None:
    current_version = _read_schema_version(
        connection
    )

    if current_version > CURRENT_SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"database schema version "
            f"{current_version} is newer than supported "
            f"version {CURRENT_SCHEMA_VERSION}"
        )

    if current_version == CURRENT_SCHEMA_VERSION:
        return

    with connection:
        connection.execute("BEGIN IMMEDIATE")

        for target_version in range(
            current_version + 1,
            CURRENT_SCHEMA_VERSION + 1,
        ):
            migration = MIGRATIONS[target_version]
            migration(connection)

            connection.execute(
                f"PRAGMA user_version = {target_version}"
            )
