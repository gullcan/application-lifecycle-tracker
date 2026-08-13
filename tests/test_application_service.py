from datetime import UTC, datetime

import pytest
from application_tracker.domain.models import (
    ApplicationStatus,
)
from application_tracker.repositories import(
    InMemoryApplicationRepository,
)
from application_tracker.services import ApplicationService

def test_service_creates_and_stores_application() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)

    application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    stored_application = repository.get(application.id)

    assert stored_application is application
    assert application.company_name == "OpenAI"
    assert application.job_title =="Backend Engineer"
    assert application.status is ApplicationStatus.DRAFT


def test_service_passes_optional_data_to_application() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    follow_up_at = datetime(
        2026,
        8,
        15,
        9,
        30,
        tzinfo=UTC,
    )
    application = service.create_application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.APPLIED,
        follow_up_at=follow_up_at,
    )

    assert application.status is ApplicationStatus.APPLIED
    assert application.follow_up_at == follow_up_at
    assert repository.get(application.id) is application


def test_service_does_not_store_invalid_application() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)

    with pytest.raises(
        ValueError,
        match="company_name cannot be blank",
    ):
        service.create_application(
            company_name=" ",
            job_title="Backend Engineer",
        )

        assert repository.list_all() == []
