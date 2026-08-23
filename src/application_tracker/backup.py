import argparse
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from application_tracker.config import Settings


def create_database_backup(
    source: Path,
    destination: Path,
) -> Path:
    if not source.exists():
        raise FileNotFoundError(
            f"database file '{source}' does not exist"
        )
    if source.resolve() == destination.resolve():
        raise ValueError(
            "backup destination must differ from source"
        )
    if destination.exists():
        raise FileExistsError(
            f"backup file '{destination}' already exists"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    source_connection = sqlite3.connect(source)
    destination_connection = sqlite3.connect(destination)

    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()

    return destination


def restore_database_backup(
    backup: Path,
    destination: Path,
) -> Path:
    if not backup.exists():
        raise FileNotFoundError(
            f"backup file '{backup}' does not exist"
        )
    if backup.resolve() == destination.resolve():
        raise ValueError(
            "backup source must differ from destination"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    backup_connection = sqlite3.connect(
        f"file:{backup}?mode=ro",
        uri=True,
    )
    destination_connection = sqlite3.connect(destination)

    try:
        integrity_result = backup_connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        if integrity_result != "ok":
            raise ValueError("backup database is not valid")

        backup_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        backup_connection.close()

    return destination


def default_backup_path() -> Path:
    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    return Path("backups") / (
        f"application_tracker_{timestamp}.db"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Back up or restore the SQLite database.",
    )
    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )
    backup_command = commands.add_parser("backup")
    backup_command.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=default_backup_path(),
    )
    restore_command = commands.add_parser("restore")
    restore_command.add_argument(
        "backup",
        type=Path,
    )
    arguments = parser.parse_args()
    settings = Settings.from_environment()
    if arguments.command == "backup":
        destination = create_database_backup(
            settings.database_path,
            arguments.destination,
        )
    else:
        destination = restore_database_backup(
            arguments.backup,
            settings.database_path,
        )
    print(destination)


if __name__ == "__main__":
    main()
