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
    # Arrange: Repository oluştur → Service oluştur → APPLIED durumunda Application kaydet

    updated_application = service.change_application_status(
        application_id=application.id,
        new_status=ApplicationStatus.SCREENING,
    )
    # Act: Service’e Application UUID’sini ve SCREENING status’unu ver

    stored_application = repository.get(application.id)
    status_change = application.status_history[-1] # listenin veya tuple’ın son elemanını getirir. Python’da -1, sondan ilk elemanı ifade eder.

    assert updated_application is application
    assert stored_application is application
    assert application.status is ApplicationStatus.SCREENING
    assert status_change.previous_status is ApplicationStatus.APPLIED
    assert status_change.new_status is ApplicationStatus.SCREENING

    # Assert: Dönen nesne aynı Application mı? Repository güncel nesneyi görüyor mu? Status değişti mi? History doğru geçişi içeriyor mu?

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

# Service UUID'yi repository'ye verir → repository kayıt bulamaz → ApplicationNotFoundError üretir → service hatayı gizlemez → caller anlamlı hatayı alır


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


def test_service_schedule_follow_up_for_selected_application() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    target_application = service.create_application( # tarih atanmalı
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    other_application = service.create_application( # değişmemeli
        company_name="Anthropic",
        job_title="Python Engineer",
    )
    deadline = datetime(
        2026,
        8,
        20,
        9,
        30,
        tzinfo=UTC,
    )

    updated_application = (
        service.schedule_application_follow_up(
            application_id=target_application.id,
            follow_up_at=deadline,
        )
    )

    assert updated_application is target_application
    assert target_application.follow_up_at == deadline
    assert other_application.follow_up_at is None


def test_service_clears_application_follow_up() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=datetime(
            2026,
            8,
            20,
            9,
            30,
            tzinfo=UTC,
        ),
    )

    updated_application = (
        service.clear_application_follow_up(
            application_id=application.id,
        )
    )
    assert updated_application is application
    assert application.follow_up_at is None


def test_service_preserves_follow_up_when_rescheduling_fails() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    original_deadline = datetime(
        2026,
        8,
        20,
        9,
        30,
        tzinfo=UTC,
    )
    application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=original_deadline,
    )
    naive_deadline = datetime(
        2026,
        8,
        25,
        9,
        30,
    )

    with pytest.raises(
        ValueError,
        match="follow_up_at must be timezone-aware",
    ):
        service.schedule_application_follow_up(
            application_id=application.id,
            follow_up_at=naive_deadline,
        )

    assert application.follow_up_at == original_deadline


def test_service_lists_all_applications() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    first_application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    second_application = service.create_application(
        company_name="Anthropic",
        job_title="Python Engineer",
    )

    applications = service.list_applications()
    applications_ids = {
        application.id
        for application in applications
    }

    assert applications_ids == {
        first_application.id,
        second_application.id,
    }

def test_services_filters_applications_by_status() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    applied_applications = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    interview_application = service.create_application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
    )

    applications = service.list_applications(
        status=ApplicationStatus.INTERVIEW,
    )

    assert applications == [interview_application]
    assert applied_applications not in applications


def test_service_lists_applications_needing_follow_up() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    as_of = datetime(2026, 8, 20, tzinfo=UTC)

    due_application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        follow_up_at=datetime(
            2026,
            8,
            19,
            tzinfo=UTC,
        ),
    )
    service.create_application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
        follow_up_at=datetime(
            2026,
            8,
            21,
            tzinfo=UTC,
        ),
    )
    service.create_application(
        company_name="Github",
        job_title="Platform Engineer",
        status=ApplicationStatus.REJECTED,
        follow_up_at=datetime(
            2026,
            8,
            18,
            tzinfo=UTC,
        ),
    )

    applications = (
        service.list_applications_needing_follow_up(
            as_of=as_of,
        )
    )

    assert applications == [due_application]

def test_follow_up_list_rejects_naive_as_of() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)
    naive_as_of = datetime(2026, 8, 20)

    with pytest.raises(
        ValueError,
        match="as_of must be timezone-aware",
    ):
        service.list_applications_needing_follow_up(
            as_of=naive_as_of,
        )
