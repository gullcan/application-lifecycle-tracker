import pytest
from application_tracker.domain.models import Application, ApplicationStatus


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