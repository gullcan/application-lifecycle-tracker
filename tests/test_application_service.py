from datetime import UTC, datetime

import pytest
from application_tracker.domain.models import (
    ApplicationStatus,
)
from application_tracker.repositories import(
    ApplicationNotFoundError,
    InMemoryApplicationRepository,
)
from application_tracker.services import ApplicationService

from uuid import uuid4

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

def test_service_changes_application_status() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    #Arrange: Repository oluştur → Service oluştur → APPLIED durumunda Application kaydet

    updated_application = service.change_application_status(
        application_id=application.id,
        new_status=ApplicationStatus.SCREENING,
    )
    #Act: Service’e Application UUID’sini ve SCREENING status’unu ver

    stored_application = repository.get(application.id)
    status_change = application.status_history[-1] # listenin veya tuple’ın son elemanını getirir. Python’da -1, sondan ilk elemanı ifade eder.

    assert updated_application is application
    assert stored_application is application
    assert application.status is ApplicationStatus.SCREENING
    assert status_change.previous_status is ApplicationStatus.APPLIED
    assert status_change.new_status is ApplicationStatus.SCREENING

    #Assert: Dönen nesne aynı Application mı? Repository güncel nesneyi görüyor mu? Status değişti mi? History doğru geçişi içeriyor mu?

def test_status_change_raises_error_for_unknown_application() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    missing_id = uuid4()

    with pytest.raises(
        ApplicationNotFoundError,
        match=str(missing_id),
    ):
        service.change_application_status(
            application_id=missing_id,
            new_status=ApplicationStatus.INTERVIEW,
        )

#Service UUID'yi repository'ye verir → repository kayıt bulamaz → ApplicationNotFoundError üretir → service hatayı gizlemez → caller anlamlı hatayı alır


def test_service_preserves_state_when_status_change_fails() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.REJECTED,
    )

    with pytest.raises(ValueError, match="terminal status"):
        service.change_application_status(
            application_id=application.id,
            new_status=ApplicationStatus.INTERVIEW,
        )

    assert application.status is ApplicationStatus.REJECTED
    assert application.status_history == ()
    