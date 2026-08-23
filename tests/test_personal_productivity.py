from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from application_tracker.api import create_app
from application_tracker.domain.models import (
    Application,
    ApplicationSource,
    ApplicationStatus,
)
from application_tracker.repositories import (
    ApplicationSort,
    InMemoryApplicationRepository,
)
from application_tracker.sqlite_repository import (
    SQLiteApplicationRepository,
)


def test_application_updates_personal_tracking_details() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )

    application.update_details(
        company_name="Anthropic",
        job_title="Python Engineer",
        source=ApplicationSource.REFERRAL,
        job_url="https://example.com/jobs/1",
        notes="Talk to the hiring manager.",
    )

    assert application.company_name == "Anthropic"
    assert application.job_title == "Python Engineer"
    assert application.source is ApplicationSource.REFERRAL
    assert application.job_url == "https://example.com/jobs/1"
    assert application.notes == "Talk to the hiring manager."


def test_application_rejects_invalid_source_and_job_url() -> None:
    with pytest.raises(TypeError, match="ApplicationSource"):
        Application(
            company_name="OpenAI",
            job_title="Engineer",
            source="linkedin",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="job_url"):
        Application(
            company_name="OpenAI",
            job_title="Engineer",
            job_url=" ",
        )


@pytest.mark.parametrize(
    ("company_name", "job_title", "source", "job_url"),
    [
        (" ", "Engineer", None, None),
        ("OpenAI", " ", None, None),
        ("OpenAI", "Engineer", "linkedin", None),
        ("OpenAI", "Engineer", None, " "),
    ],
)
def test_application_rejects_invalid_personal_details(
    company_name: str,
    job_title: str,
    source: object,
    job_url: str | None,
) -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Engineer",
    )

    with pytest.raises((TypeError, ValueError)):
        application.update_details(
            company_name=company_name,
            job_title=job_title,
            source=source,  # type: ignore[arg-type]
            job_url=job_url,
            notes="",
        )


def test_archived_application_does_not_need_follow_up() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        follow_up_at=datetime(2026, 8, 20, tzinfo=UTC),
    )

    application.archive()

    assert application.archived_at is not None
    assert not application.needs_follow_up(
        datetime(2026, 8, 21, tzinfo=UTC)
    )

    with pytest.raises(ValueError, match="archived application"):
        application.change_status(ApplicationStatus.SCREENING)

    with pytest.raises(ValueError, match="archived application"):
        application.schedule_follow_up(
            datetime(2026, 8, 22, tzinfo=UTC)
        )

    application.restore_from_archive()

    assert application.archived_at is None

    with pytest.raises(ValueError, match="not archived"):
        application.restore_from_archive()


def test_repository_searches_sorts_and_hides_archived() -> None:
    repository = InMemoryApplicationRepository()
    openai = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        notes="Remote Python role",
    )
    anthropic = Application(
        company_name="Anthropic",
        job_title="Platform Engineer",
    )
    repository.add(openai)
    repository.add(anthropic)
    anthropic.archive()

    assert repository.list_all(search="python") == [openai]
    assert repository.list_all(
        include_archived=True,
        sort=ApplicationSort.COMPANY_ASC,
    ) == [anthropic, openai]


def test_sqlite_round_trips_personal_tracking_details(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"
    repository = SQLiteApplicationRepository(database_path)
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        source=ApplicationSource.LINKEDIN,
        job_url="https://example.com/jobs/1",
        notes="Portfolio sent.",
    )
    application.archive()
    repository.add(application)

    restored = SQLiteApplicationRepository(
        database_path
    ).get(application.id)

    assert restored.source is ApplicationSource.LINKEDIN
    assert restored.job_url == "https://example.com/jobs/1"
    assert restored.notes == "Portfolio sent."
    assert restored.archived_at == application.archived_at

    search_results = repository.list_all(
        search="portfolio",
        include_archived=True,
        sort=ApplicationSort.CREATED_DESC,
    )
    assert [result.id for result in search_results] == [
        restored.id
    ]


def test_api_updates_archives_searches_and_exports() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    update_response = client.patch(
        f"/applications/{application.id}",
        json={
            "company_name": "OpenAI",
            "job_title": "Senior Backend Engineer",
            "source": "company_website",
            "job_url": "https://example.com/jobs/1",
            "notes": "Follow up with the recruiter.",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["source"] == "company_website"

    search_response = client.get(
        "/applications",
        params={"q": "recruiter"},
    )
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1

    archive_response = client.put(
        f"/applications/{application.id}/archive"
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["archived_at"] is not None
    duplicate_archive_response = client.put(
        f"/applications/{application.id}/archive"
    )
    assert duplicate_archive_response.status_code == 409
    archived_follow_up_response = client.put(
        f"/applications/{application.id}/follow-up",
        json={
            "follow_up_at": "2026-08-25T09:00:00+00:00",
        },
    )
    assert archived_follow_up_response.status_code == 409
    assert client.get("/applications").json() == []
    assert len(
        client.get(
            "/applications",
            params={"include_archived": True},
        ).json()
    ) == 1

    export_response = client.get("/applications/export.csv")
    assert export_response.status_code == 200
    assert "Senior Backend Engineer" in export_response.text
    assert (
        export_response.headers["content-type"]
        == "text/csv; charset=utf-8"
    )

    restore_response = client.delete(
        f"/applications/{application.id}/archive"
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["archived_at"] is None

    duplicate_restore_response = client.delete(
        f"/applications/{application.id}/archive"
    )
    assert duplicate_restore_response.status_code == 409
