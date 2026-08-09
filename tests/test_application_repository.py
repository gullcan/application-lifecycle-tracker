from uuid import uuid4

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
            "interview", #type: ignnore[arg-type]
        )