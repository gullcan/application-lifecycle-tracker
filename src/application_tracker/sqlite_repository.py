import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID
from application_tracker.domain.models import(
    Application,
    ApplicationStatus,
    ApplicationStatusChange,
)
from application_tracker.repositories import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
)
from application_tracker.domain.validation import (
    require_timezone_aware,
)

class SQLiteApplicationRepository:
    def __init__(
            self,
            database_path: str | Path,
    ) -> None:
        self._database_path = str(database_path)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _create_schema(self) -> None:
        connection = self._connect()

        try:
            with connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS applications(
                        id TEXT PRIMARY KEY,
                        company_name TEXT NOT NULL,
                        job_title TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        follow_up_at TEXT
                    );
                    
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
                    );

                    """
                )

        finally:
            connection.close()


    def add(self, application: Application) -> None:
        connection = self._connect()

        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO applications(
                    id,
                    company_name,
                    job_title,
                    status,
                    created_at,
                    follow_up_at
                    )
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(application.id),
                        application.company_name,
                        application.job_title,
                        application.status.value,
                        application.created_at.isoformat(),
                        (
                            application.follow_up_at.isoformat()
                            if application.follow_up_at is not None
                            else None
                        ),                    
                    ),
                )

                connection.executemany(
                    """
                    INSERT INTO application_status_changes (
                        application_id,
                        sequence_number,
                        previous_status,
                        new_status,
                        changed_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                        
                    """,
                    (
                        (
                            str(application.id),
                            sequence_number,
                            status_change.previous_status.value,
                            status_change.new_status.value,
                            status_change.changed_at.isoformat(),
                        )
                        for sequence_number, status_change
                        in enumerate(application.status_history)
                    ),
                )
            
        except sqlite3.IntegrityError as error:
            raise DuplicateApplicationError(
                f"application with id "
                f"'{application.id}' already exists"
            ) from error
        finally:
            connection.close()


    def get(self, application_id: UUID) -> Application:
        connection = self._connect()

        try:
            application_row = connection.execute(
                """
                SELECT
                    id,
                    company_name,
                    job_title,
                    status,
                    created_at,
                    follow_up_at
                FROM applications
                WHERE id = ?
                """,
                (str(application_id),),   
            ).fetchone()

            if application_row is None:
                raise ApplicationNotFoundError(
                    f"application with id "
                    f"'{application_id}' was not found"
                )
            history_rows = connection.execute(
                 """
                 SELECT
                    previous_status,
                    new_status,
                    changed_at
                FROM application_status_changes
                WHERE application_id = ?
                ORDER BY sequence_number
                """,
                (str(application_id),),
            ).fetchall()
        finally:
            connection.close()

        status_history = tuple(
            ApplicationStatusChange(
                previous_status=ApplicationStatus(
                    row["previous_status"]
                ),
                new_status=ApplicationStatus(
                    row["new_status"]
                ),
                changed_at=datetime.fromisoformat(
                    row["changed_at"]
                ),
            )
            for row in history_rows
        )
        follow_up_value = application_row["follow_up_at"]

        return Application.restore(
            application_id=UUID(application_row["id"]),
            company_name=application_row["company_name"],
            job_title=application_row["job_title"],
            status=ApplicationStatus(application_row["status"]),
            created_at=datetime.fromisoformat(
                application_row["created_at"]
            ),
            follow_up_at=(
                datetime.fromisoformat(follow_up_value)
                if follow_up_value is not None
                else None
            ),
            status_history=status_history,
        )
    
    def list_all(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Application]:
        connection = self._connect()
        effective_limit = (
            -1
            if limit is None
            else limit
        )

        try:
            rows = connection.execute(
                """
                SELECT id
                FROM applications
                ORDER BY created_at, id
                LIMIT ? OFFSET ?
                """,
                (
                    effective_limit,
                    offset,
                ),
            ).fetchall()
        finally:
            connection.close()

        return [
            self.get(UUID(row["id"]))
            for row in rows
        ]
    
    def find_by_status(
        self,
        status: ApplicationStatus,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Application]:
        if not isinstance(status, ApplicationStatus):
            raise TypeError(
                "status must be an ApplicationStatus"
            )

        connection = self._connect()
        effective_limit = (
            -1
            if limit is None
            else limit
        )

        try:
            rows = connection.execute(
                """
                SELECT id
                FROM applications
                WHERE status = ?
                ORDER BY created_at, id
                LIMIT ? OFFSET ?
                """,
                (
                    status.value,
                    effective_limit,
                    offset,
                ),
            ).fetchall()
        finally:
            connection.close()

        return [
            self.get(UUID(row["id"]))
            for row in rows
        ]

    def find_needing_follow_up(
            self,
            as_of: datetime,
    ) -> list[Application]:
        require_timezone_aware(as_of, "as_of")

        return [
            application
            for application in self.list_all()
            if application.needs_follow_up(as_of)
        ]
            

    def save(self, application: Application) -> None:
        connection = self._connect()

        try: 
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE applications
                    SET
                        company_name = ?,
                        job_title = ?,
                        status = ?,
                        created_at = ?,
                        follow_up_at = ?
                    WHERE id = ?
                    """,
                    (
                        application.company_name,
                        application.job_title,
                        application.status.value,
                        application.created_at.isoformat(),
                        (
                            application.follow_up_at.isoformat()
                            if application.follow_up_at is not None
                            else None
                        ),
                        str(application.id),
                    ),
                )
                if cursor.rowcount == 0:
                    raise ApplicationNotFoundError(
                        f"application with id "
                        f"'{application.id}' was not found"
                    )

                connection.execute(
                    """
                    DELETE FROM application_status_changes
                    WHERE application_id = ?
                    """,
                    (str(application.id),),
                )
                connection.executemany(
                    """
                    INSERT INTO application_status_changes (
                        application_id,
                        sequence_number,
                        previous_status,
                        new_status,
                        changed_at
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        (
                            str(application.id),
                            sequence_number,
                            status_change.previous_status.value,
                            status_change.new_status.value,
                            status_change.changed_at.isoformat(),
                        )
                        for sequence_number, status_change
                        in enumerate(application.status_history)
                    ),
                )
            
        finally:
            connection.close()
