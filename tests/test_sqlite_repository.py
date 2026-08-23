from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)
from application_tracker.repositories import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
)
from application_tracker.sqlite_repository import (
    SQLiteApplicationRepository,
)
import sqlite3

from application_tracker.migrations import (
    CURRENT_SCHEMA_VERSION,
)

def test_sqlite_repository_persists_application_across_instances(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"

    writer = SQLiteApplicationRepository(database_path)
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        follow_up_at=datetime(2026, 8, 20, tzinfo=UTC),
    )
    application.change_status(ApplicationStatus.SCREENING)

    writer.add(application)

    reader = SQLiteApplicationRepository(database_path)
    restored = reader.get(application.id)

    assert restored is not application
    assert restored.id == application.id
    assert restored.company_name == application.company_name
    assert restored.job_title == application.job_title
    assert restored.status is application.status
    assert restored.created_at == application.created_at
    assert restored.follow_up_at == application.follow_up_at
    assert restored.status_history == application.status_history


def test_sqlite_repository_rejects_duplicate_application(
        tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "applications.db"
    )
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    repository.add(application)

    with pytest.raises(
        DuplicateApplicationError,
        match=str(application.id),
    ):
        repository.add(application)


def test_sqlite_repository_raises_error_for_unknown_application(
        tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "application.db"
    )
    unknown_id = uuid4()

    with pytest.raises(
        ApplicationNotFoundError,
        match=str(unknown_id),
    ):
        repository.get(unknown_id)


def test_sqlite_repository_lists_all_applications(
        tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "applications.db"
    )
    first = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    second = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
    )
    repository.add(first)
    repository.add(second)

    applications = repository.list_all()

    assert {
        application.id
        for application in applications
    } == {first.id, second.id}


def test_sqlite_repository_finds_applications_by_status(
        tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "applications.db"
    )
    applied = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    interview = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
    )
    repository.add(applied)
    repository.add(interview)

    applications = repository.find_by_status(
        ApplicationStatus.INTERVIEW
    )

    assert [application.id for application in applications] == [
        interview.id
    ]


def test_sqlite_repository_finds_applications_needing_follow_up(
        tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "applications.db"
    )
    as_of = datetime(2026, 8, 20, tzinfo=UTC)

    due = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        follow_up_at=datetime(2026, 8, 19, tzinfo=UTC),
    )
    future = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
        follow_up_at=datetime(2026, 8, 21, tzinfo=UTC),
    )
    terminal = Application(
        company_name="GitHub",
        job_title="Platform Engineer",
        status=ApplicationStatus.REJECTED,
        follow_up_at=datetime(2026, 8, 18, tzinfo=UTC),
    )

    repository.add(due)
    repository.add(future)
    repository.add(terminal)

    applications = repository.find_needing_follow_up(as_of)

    assert [application.id for application in applications] == [
        due.id
    ]


def test_sqlite_follow_up_query_rejects_naive_datetime(
        tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "applications.db"
    )

    with pytest.raises(
        ValueError,
        match="as_of must be timezone-aware",
    ):
        repository.find_needing_follow_up(
            datetime(2026, 8, 20)
        )


def test_sqlite_repository_saves_application_changes(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    repository = SQLiteApplicationRepository(database_path)
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    repository.add(application)

    application.change_status(ApplicationStatus.SCREENING)
    application.schedule_follow_up(
        datetime(2026, 8, 25, tzinfo=UTC)
    )
    repository.save(application)

    reader = SQLiteApplicationRepository(database_path)
    restored = reader.get(application.id)

    assert restored.status is ApplicationStatus.SCREENING
    assert restored.follow_up_at == datetime(
        2026,
        8,
        25,
        tzinfo=UTC,
    )
    assert restored.status_history == application.status_history


def test_sqlite_repository_rejects_save_for_unknown_application(
        tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "application.db"
    )
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    with pytest.raises(
        ApplicationNotFoundError,
        match=str(application.id),
    ):
        repository.save(application)

def test_sqlite_repository_paginates_applications(
    tmp_path: Path,
) -> None:
    repository = SQLiteApplicationRepository(
        tmp_path / "applications.db"
    )

    for company_name in [
        "OpenAI",
        "Anthropic",
        "GitHub",
    ]:
        repository.add(
            Application(
                company_name=company_name,
                job_title="Backend Engineer",
            )
        )

    all_applications = repository.list_all()

    page = repository.list_all(
        limit=1,
        offset=1,
    )

    assert [
        application.id
        for application in page
    ] == [all_applications[1].id]

def test_sqlite_repository_applies_current_schema_version(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"

    SQLiteApplicationRepository(database_path)

    connection = sqlite3.connect(database_path)

    try:
        schema_version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]
    finally:
        connection.close()

    assert schema_version == CURRENT_SCHEMA_VERSION

def test_sqlite_repository_upgrades_legacy_database_without_data_loss(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    application_id = uuid4()
    created_at = datetime(
        2026,
        8,
        23,
        9,
        tzinfo=UTC,
    )

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
                str(application_id),
                "OpenAI",
                "Backend Engineer",
                "applied",
                created_at.isoformat(),
                None,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    repository = SQLiteApplicationRepository(
        database_path
    )
    restored = repository.get(application_id)

    assert restored.id == application_id
    assert restored.company_name == "OpenAI"
    assert restored.job_title == "Backend Engineer"
    assert restored.status is ApplicationStatus.APPLIED
    assert restored.created_at == created_at
