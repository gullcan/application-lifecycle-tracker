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

def test_application_status_can_change() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    application.change_status(ApplicationStatus.SCREENING)

    assert application.status is ApplicationStatus.SCREENING

@pytest.mark.parametrize(
    "terminal_status",
    [
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
)

def test_terminal_application_status_cannot_change(
    terminal_status: ApplicationStatus,
) -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backen Engineer",
        status=terminal_status,
    )

    with pytest.raises(ValueError, match="terminal status"):
        application.change_status(ApplicationStatus.INTERVIEW)

    assert application.status is terminal_status

def test_application_cannot_change_to_its_current_status() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )

    with pytest.raises(ValueError, match="different from current status"):
        application.change_status(ApplicationStatus.APPLIED)

    assert application.status is ApplicationStatus.APPLIED

def test_status_change_rejects_non_enum_value() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )

    with pytest.raises(
        TypeError,
        match="new_status must be an ApplicationStatus",
    ):
        application.change_status(
            "interview", #type: ignore[arg-type]
        )

    assert application.status is ApplicationStatus.DRAFT

def test_new_application_has_empty_status_history() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    assert application.status_history == ()

def test_successful_status_change_is_recorded() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    assert application.status_history == ()

def test_successful_status_change_is_recorded() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    before_change = datetime.now(UTC)

    application.change_status(ApplicationStatus.SCREENING)

    after_change = datetime.now(UTC)
    status_change = application.status_history[0]

    assert status_change.previous_status is ApplicationStatus.APPLIED
    assert status_change.new_status is ApplicationStatus.SCREENING
    assert before_change <= status_change.changed_at <= after_change
    assert status_change.changed_at.utcoffset() == timedelta(0)

def test_status_changes_are_stored_in_chronological_order() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )

    application.change_status(ApplicationStatus.APPLIED)
    application.change_status(ApplicationStatus.SCREENING)

    transitions = [
        (change.previous_status, change.new_status)
        for change in application.status_history
    ]

    assert transitions == [
        (ApplicationStatus.DRAFT, ApplicationStatus.APPLIED),
        (ApplicationStatus.APPLIED, ApplicationStatus.SCREENING),
    ]

def test_failed_status_change_is_not_recorded() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.REJECTED,
    )

    with pytest.raises(ValueError, match="terminal status"):
        application.change_status(ApplicationStatus.INTERVIEW)

    assert application.status_history == ()