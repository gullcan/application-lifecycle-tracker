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

        