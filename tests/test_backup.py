import sqlite3
import sys
from pathlib import Path

import pytest

from application_tracker.backup import (
    create_database_backup,
    main,
    restore_database_backup,
)


def test_create_database_backup_copies_consistent_database(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "backups" / "backup.db"
    connection = sqlite3.connect(source)
    connection.execute("CREATE TABLE example (value TEXT)")
    connection.execute(
        "INSERT INTO example VALUES (?)",
        ("persisted",),
    )
    connection.commit()
    connection.close()

    result = create_database_backup(
        source,
        destination,
    )

    backup_connection = sqlite3.connect(destination)
    try:
        stored_value = backup_connection.execute(
            "SELECT value FROM example"
        ).fetchone()[0]
    finally:
        backup_connection.close()

    assert result == destination
    assert stored_value == "persisted"


def test_database_backup_refuses_to_overwrite_file(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "backup.db"
    sqlite3.connect(source).close()
    destination.touch()

    with pytest.raises(FileExistsError):
        create_database_backup(source, destination)


def test_restore_database_backup_replaces_destination(
    tmp_path: Path,
) -> None:
    backup = tmp_path / "backup.db"
    destination = tmp_path / "application.db"
    backup_connection = sqlite3.connect(backup)
    backup_connection.execute(
        "CREATE TABLE example (value TEXT)"
    )
    backup_connection.execute(
        "INSERT INTO example VALUES ('restored')"
    )
    backup_connection.commit()
    backup_connection.close()
    sqlite3.connect(destination).close()

    restore_database_backup(backup, destination)

    destination_connection = sqlite3.connect(destination)
    try:
        stored_value = destination_connection.execute(
            "SELECT value FROM example"
        ).fetchone()[0]
    finally:
        destination_connection.close()

    assert stored_value == "restored"


def test_backup_rejects_missing_and_same_paths(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.db"

    with pytest.raises(FileNotFoundError):
        create_database_backup(
            missing,
            tmp_path / "backup.db",
        )

    source = tmp_path / "source.db"
    sqlite3.connect(source).close()

    with pytest.raises(ValueError):
        create_database_backup(source, source)

    with pytest.raises(FileNotFoundError):
        restore_database_backup(missing, source)

    with pytest.raises(ValueError):
        restore_database_backup(source, source)


def test_backup_cli_creates_and_restores_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "application.db"
    backup = tmp_path / "backup.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE example (value TEXT)")
    connection.execute("INSERT INTO example VALUES ('original')")
    connection.commit()
    connection.close()
    monkeypatch.setenv(
        "APPLICATION_TRACKER_DATABASE_PATH",
        str(database),
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["backup", "backup", str(backup)],
    )
    main()

    connection = sqlite3.connect(database)
    connection.execute("UPDATE example SET value = 'changed'")
    connection.commit()
    connection.close()

    monkeypatch.setattr(
        sys,
        "argv",
        ["backup", "restore", str(backup)],
    )
    main()

    connection = sqlite3.connect(database)
    try:
        value = connection.execute(
            "SELECT value FROM example"
        ).fetchone()[0]
    finally:
        connection.close()

    assert value == "original"
