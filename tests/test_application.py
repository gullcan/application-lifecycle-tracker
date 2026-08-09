import pytest
from application_tracker.domain.models import Application, ApplicationStatus
from datetime import UTC, datetime, timedelta
from uuid import UUID


def test_application_is_created_in_draft_status() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    assert application.company_name == "OpenAI"
    assert application.job_title == "Backend Engineer"
    assert application.status is ApplicationStatus.DRAFT


def test_application_rejects_blank_company_name() -> None:
    with pytest.raises(ValueError, match= "company_name cannot be blank"):
        Application(
            company_name=" ",
            job_title="Backend Engineer",
        )

def test_application_rejects_blank_job_title() -> None:
    with pytest.raises(ValueError, match="job_title cannot be blank"):
        Application(
            company_name="OpenAI",
            job_title=" ",
        )

def test_application_rejects_status_that_is_not_an_enum() -> None:
    with pytest.raises(TypeError, match="status must be an ApplicationStatus"):
        Application(
            company_name="OpenAI",
            job_title="Backend Engineer",
            status="unknown", #type: ignore[arg-type]
        )

def test_each_application_gets_a_unique_id() -> None:
    first_application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    second_application = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
    )

    assert isinstance(first_application.id, UUID)
    assert isinstance(second_application.id, UUID)
    assert first_application.id != second_application.id

def test_application_records_creation_time_in_utc() -> None:
    before_creation = datetime.now(UTC)

    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )

    after_creation = datetime.now(UTC)

    assert before_creation <= application.created_at <= after_creation
    assert application.created_at.utcoffset() == timedelta(0)
