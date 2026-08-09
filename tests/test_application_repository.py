from uuid import uuid4

import pytest
from application_tracker.domain.models import Application
from application_tracker.repositories import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
    InMemoryApplicationRepository,
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

    