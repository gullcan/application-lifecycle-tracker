import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID
from application_tracker.domain.models import(
    Application,
    ApplicationSource,
    ApplicationStatus,
    ApplicationStatusChange,
)
from application_tracker.repositories import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
    ApplicationSort,
)
from application_tracker.domain.validation import (
    require_timezone_aware,
)
from application_tracker.migrations import (
    migrate_database,
)

class SQLiteApplicationRepository:
    def __init__(
            self,
            database_path: str | Path,
    ) -> None:
        self._database_path = str(database_path)
        self._migrate_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _migrate_schema(self) -> None:
        connection = self._connect()

        try:
            migrate_database(connection)
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
                    follow_up_at,
                    source,
                    job_url,
                    notes,
                    archived_at
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        (
                            application.source.value
                            if application.source is not None
                            else None
                        ),
                        application.job_url,
                        application.notes,
                        (
                            application.archived_at.isoformat()
                            if application.archived_at is not None
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
                    follow_up_at,
                    source,
                    job_url,
                    notes,
                    archived_at
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
        source_value = application_row["source"]
        archived_at_value = application_row["archived_at"]

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
            source=(
                ApplicationSource(source_value)
                if source_value is not None
                else None
            ),
            job_url=application_row["job_url"],
            notes=application_row["notes"],
            archived_at=(
                datetime.fromisoformat(archived_at_value)
                if archived_at_value is not None
                else None
            ),
            status_history=status_history,
        )

    def list_all(
        self,
        *,
        search: str | None = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
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
            rows = self._query_application_ids(
                connection,
                status=None,
                search=search,
                include_archived=include_archived,
                sort=sort,
                limit=effective_limit,
                offset=offset,
            )
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
        search: str | None = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
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
            rows = self._query_application_ids(
                connection,
                status=status,
                search=search,
                include_archived=include_archived,
                sort=sort,
                limit=effective_limit,
                offset=offset,
            )
        finally:
            connection.close()

        return [
            self.get(UUID(row["id"]))
            for row in rows
        ]

    def _query_application_ids(
        self,
        connection: sqlite3.Connection,
        *,
        status: ApplicationStatus | None,
        search: str | None,
        include_archived: bool,
        sort: ApplicationSort,
        limit: int,
        offset: int,
    ) -> list[sqlite3.Row]:
        if not isinstance(sort, ApplicationSort):
            raise TypeError("sort must be an ApplicationSort")

        conditions: list[str] = []
        parameters: list[object] = []

        if status is not None:
            conditions.append("status = ?")
            parameters.append(status.value)
        if not include_archived:
            conditions.append("archived_at IS NULL")
        if search is not None and search.strip():
            conditions.append(
                """
                lower(
                    company_name || ' ' || job_title || ' ' ||
                    notes || ' ' || coalesce(source, '')
                ) LIKE ?
                """
            )
            parameters.append(
                f"%{search.strip().lower()}%"
            )

        where_clause = (
            f"WHERE {' AND '.join(conditions)}"
            if conditions
            else ""
        )
        order_clause = {
            ApplicationSort.CREATED_ASC: "created_at ASC, id ASC",
            ApplicationSort.CREATED_DESC: "created_at DESC, id DESC",
            ApplicationSort.COMPANY_ASC: (
                "company_name COLLATE NOCASE ASC, "
                "created_at ASC, id ASC"
            ),
        }[sort]
        parameters.extend((limit, offset))

        return connection.execute(
            f"""
            SELECT id
            FROM applications
            {where_clause}
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
            """,
            parameters,
        ).fetchall()

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
                        follow_up_at = ?,
                        source = ?,
                        job_url = ?,
                        notes = ?,
                        archived_at = ?
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
                        (
                            application.source.value
                            if application.source is not None
                            else None
                        ),
                        application.job_url,
                        application.notes,
                        (
                            application.archived_at.isoformat()
                            if application.archived_at is not None
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
