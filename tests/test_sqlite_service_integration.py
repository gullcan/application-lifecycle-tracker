from datetime import UTC, datetime
from pathlib import Path
from application_tracker.domain.models import (
    ApplicationStatus,
)
from application_tracker.services import ApplicationService
from application_tracker.sqlite_repository import (
    SQLiteApplicationRepository,
)

def test_services_persists_status_change_with_sqlite(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    service = ApplicationService(
        SQLiteApplicationRepository(database_path)
    )
    application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    service.change_application_status(
        application_id=application.id,
        new_status=ApplicationStatus.SCREENING
    )

    restored = SQLiteApplicationRepository(
        database_path
    ).get(application.id)

    assert restored.status is ApplicationStatus.SCREENING
    assert len(restored.status_history) == 1
    assert (
        restored.status_history[0].previous_status
        is ApplicationStatus.APPLIED
    )
    assert (
        restored.status_history[0].new_status
        is ApplicationStatus.SCREENING
    )

def test_services_persists_scheduled_follow_up_with_sqlite(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    service = ApplicationService(
        SQLiteApplicationRepository(database_path)
    )
    application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    follow_up_at = datetime(
        2026,
        8,
        25,
        tzinfo=UTC,
    )

    service.schedule_application_follow_up(
        application_id=application.id,
        follow_up_at=follow_up_at,
    )

    restored = SQLiteApplicationRepository(
        database_path
    ).get(application.id)

    assert restored.follow_up_at == follow_up_at


def test_service_persist_cleared_follow_up_with_sqlite(
        tmp_path: Path,
) -> None:
    database_path = tmp_path / "applicatons.db"
    service = ApplicationService(
        SQLiteApplicationRepository(database_path)
    )
    application = service.create_application(
        company_name="Open AI",
        job_title="Backend Engineer",
        follow_up_at=datetime(
            2026,
            8,
            25,
            tzinfo=UTC,
        ),
    )

    service.clear_application_follow_up(
        application_id=application.id,
    )

    restored = SQLiteApplicationRepository(
        database_path
    ).get(application.id)

    assert restored.follow_up_at is None
