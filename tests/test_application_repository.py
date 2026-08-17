from uuid import uuid4
from datetime import UTC, datetime

import pytest

from application_tracker.domain.models import Application
from application_tracker.repositories import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
    InMemoryApplicationRepository,
)

from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)

def test_repository_adds_and_retrieves_applicaiton() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )

    repository.add(application)

    stored_application = repository.get(application.id)

    assert stored_application is application

def test_repository_raises_error_for_unknown_id() -> None:
    repository = InMemoryApplicationRepository()
    missing_id = uuid4()

    with pytest.raises(
        ApplicationNotFoundError,
        match=str(missing_id),
    ):
        repository.get(missing_id)

def test_repository_rejects_duplicate_application() -> None:
    repository = InMemoryApplicationRepository()
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

    assert repository.get(application.id) is application

def test_repository_lists_all_applications() -> None:
    repository = InMemoryApplicationRepository()
    first_application = Application(
            company_name="OpenAI",
            job_title="Backend Engineer",
        )
    second_application = Application(
            company_name="Anthropic",
            job_title="Python Engineer",
        )
    repository.add(first_application)
    repository.add(second_application)

    applications = repository.list_all()
    application_ids = {
        application.id
        for application in applications
    }
    assert application_ids == {
        first_application.id,
        second_application.id,
    }

def test_modifying_list_result_does_not_change_repository() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    repository.add(application)

    applications = repository.list_all()
    applications.clear()

    assert repository.get(application.id) is application
    assert repository.list_all() == [application]

def test_repository_finds_applications_by_status() -> None:
    repository = InMemoryApplicationRepository()
    applied_application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    interview_application = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
    )
    repository.add(applied_application)
    repository.add(interview_application)

    applications = repository.find_by_status(
        ApplicationStatus.INTERVIEW
    )
    assert applications == [interview_application]

def test_status_filter_uses_current_application_status() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="=OpenAI",
        job_title="Backend Engineer",
    )
    repository.add(application)

    application.change_status(ApplicationStatus.INTERVIEW)

    assert repository.find_by_status(
        ApplicationStatus.APPLIED
    ) == []
    assert repository.find_by_status(
        ApplicationStatus.INTERVIEW
    ) == [application]


def test_status_filter_rejcets_non_enum_value() -> None:
    repository = InMemoryApplicationRepository()

    with pytest.raises(
        TypeError,
        match="status must be an ApplicationStatus",
    ):
        repository.find_by_status(
            "interview", # type: ignnore[arg-type]
        )
def test_repository_finds_applications_needing_follow_up() -> None:
    repository = InMemoryApplicationRepository()
    as_of = datetime(2026, 8, 15, tzinfo=UTC)

    due_application = Application( # Tarih geçmiş + aktif → sonuçta olmalı
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        follow_up_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    future_application = Application( # Tarih gelmemiş → sonuçta olmamalı
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
        follow_up_at=datetime(2026, 8, 16, tzinfo=UTC),
    )
    unscheduled_application = Application( # Tarih yok → sonuçta olmamalı
        company_name="Stripe",
        job_title="Software Engineer",
        status=ApplicationStatus.APPLIED,
    )
    terminal_application = Application( # Tarih geçmiş ama rejected → sonuçta olmamalı
        company_name="Github",
        job_title="Platform Engineer",
        status=ApplicationStatus.REJECTED,
        follow_up_at=datetime(2026, 8, 13, tzinfo=UTC),
    )

    for application in ( # Application nesnelerini bir tuple içine koyup dolaşıyoruz
        due_application,
        future_application,
        unscheduled_application,
        terminal_application,
    ):
        repository.add(application)

        result = repository.find_needing_follow_up(as_of)

        assert result == [due_application]


def test_follow_up_query_rejects_naive_as_of_when_empty() -> None:
    repository = InMemoryApplicationRepository()
    naive_as_of = datetime(2026, 8, 15)

    with pytest.raises(
        ValueError,
        match="as_of must be timezone-aware",
    ):
        repository.find_needing_follow_up(naive_as_of)