import pytest
from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
    ApplicationStatusChange,
)
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4


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
            status="unknown", # type: ignore[arg-type]
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
        ApplicationStatus.ACCEPTED,
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
            "interview", # type: ignore[arg-type]
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

def test_application_status_cannot_be_assigned_directly() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    with pytest.raises(AttributeError):
        application.status = (
            ApplicationStatus.INTERVIEW
        )

    assert application.status is ApplicationStatus.APPLIED
    assert application.status_history == ()

def test_application_id_cannot_be_assigned_directly() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    original_id = application.id

    with pytest.raises(AttributeError):
        application.id = uuid4() #type : ignore[misc]

    assert application.id == original_id


def test_application_without_follow_up_date_does_not_need_follow_up() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    result = application.needs_follow_up(
        as_of=datetime(2026, 8, 11, tzinfo=UTC)
    )

    assert result is False

def test_application_with_future_follow_up_does_not_need_follow_up() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=datetime(2026, 8, 12, tzinfo=UTC)
    )

    result = application.needs_follow_up(
        as_of=datetime(2026, 8, 11, tzinfo=UTC)
    )

    assert result is False

def test_application_with_past_follow_up_needs_follow_up() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=datetime(2026, 8, 10, tzinfo=UTC)
    )
    result = application.needs_follow_up(
        as_of=datetime(2026, 8, 11, tzinfo=UTC)
    )

    assert result is True

def test_application_needs_follow_up_at_exact_deadline() -> None:
    deadline = datetime(2026, 8, 10, 9, 30, tzinfo=UTC)
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=deadline,
    )

    result = application.needs_follow_up(as_of=deadline)
    assert result is True

@pytest.mark.parametrize(
    "terminal_status",
    [
        ApplicationStatus.ACCEPTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
)
def test_terminal_application_does_not_need_follow_up(
    terminal_status: ApplicationStatus,
) -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=terminal_status,
        follow_up_at=datetime(2026, 8, 11, tzinfo=UTC)
    )
    result = application.needs_follow_up(
        as_of=datetime(2026, 8, 11, tzinfo=UTC)
    )

    assert result is False

def test_application_rejects_naive_follow_up_datetime() -> None:
    naive_follow_up = datetime(2026, 8, 10, 9, 30)

    with pytest.raises(
        ValueError,
        match="follow_up_at must be timezone-aware",
    ):
        Application(
            company_name="OpenAI",
            job_title="Backend Engineer",
            follow_up_at=naive_follow_up,
        )

def test_needs_follow_up_rejects_naive_as_of_datetime() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=datetime(
            2026,
            8,
            10,
            9,
            30,
            tzinfo=UTC,
        ),
    )
    naive_as_of = datetime(2026, 8, 11, 9,30)

    with pytest.raises(
        ValueError,
        match="as_of must be timezone-aware",
    ):
        application.needs_follow_up(as_of=naive_as_of)


def test_follow_up_can_be_scheduled_after_creation() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    deadline = datetime(
        2026,
        8,
        12,
        9,
        30,
        tzinfo=UTC
    )

    application.schedule_follow_up(deadline)

    assert application.follow_up_at == deadline
    assert application.needs_follow_up(
        as_of=deadline
    ) is True

def test_existing_follow_up_can_be_rescheduled() -> None:
    first_deadline = datetime(
        2026,
        8,
        12,
        9,
        30,
        tzinfo=UTC,
    )
    new_deadline = datetime(
        2026,
        8,
        15,
        9,
        30,
        tzinfo=UTC,
    )
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=first_deadline,
    )

    application.schedule_follow_up(new_deadline)

    assert application.follow_up_at == new_deadline
    assert application.needs_follow_up(
        as_of=first_deadline
    ) is False

def test_follow_up_can_be_cleared() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=datetime(
            2026,
            8,
            12,
            tzinfo=UTC,
        ),
    )
    application.clear_follow_up()

    assert application.follow_up_at is None
    assert application.needs_follow_up(
        as_of=datetime(2026, 8, 20, tzinfo= UTC)
    ) is False

def test_clearing_follow_up_is_idempotent() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )

    application.clear_follow_up()
    application.clear_follow_up()


    assert application.follow_up_at is None

def test_scheduling_follow_up_rejects_naive_datetime() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    naive_deadline = datetime(2026, 8, 12, 9, 30)

    with pytest.raises(
        ValueError,
        match="follow_up_at must be timezone-aware",
    ):
        application.schedule_follow_up(naive_deadline)

    assert application.follow_up_at is None

def test_follow_up_at_cannot_be_assigned_directly() -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )

    with pytest.raises(AttributeError):
        application.follow_up_at = (
            datetime(2026, 8, 12, tzinfo=UTC)
        )

    assert application.follow_up_at is None


def test_withdrawn_status_has_correct_external_value() -> None:
    assert ApplicationStatus.WITHDRAWN.value == "withdrawn"

def test_restore_preserves_persisted_applicatio_state() -> None:
    application_id = UUID(
        "12345678-1234-5678-1234-567812345678"
    )
    created_at = datetime(2026, 8, 1, tzinfo=UTC)
    follow_up_at = datetime(2026, 8, 10, tzinfo=UTC)
    status_history = (
        ApplicationStatusChange(
            previous_status=ApplicationStatus.APPLIED,
            new_status=ApplicationStatus.SCREENING,
            changed_at=datetime(2026, 8, 5, tzinfo=UTC),
        ),
    )

    application = Application.restore(
        application_id=application_id,
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.SCREENING,
        created_at=created_at,
        follow_up_at=follow_up_at,
        status_history=status_history,
    )

    assert application.id == application_id
    assert application.company_name == "OpenAI"
    assert application.job_title == "Backend Engineer"
    assert application.status is ApplicationStatus.SCREENING
    assert application.created_at == created_at
    assert application.follow_up_at == follow_up_at
    assert application.status_history == status_history

def test_restore_rejects_timezone_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="created_at must be timezone-aware",
    ):
        Application.restore(
            application_id=UUID(
                "12345678-1234-5678-1234-567812345678"
            ),
            company_name="OpenAI",
            job_title="Backend Engineer",
            status=ApplicationStatus.APPLIED,
            created_at=datetime(2026, 8, 1),
        )

def test_restore_rejects_timezone_naive_status_history() -> None:
    status_history = (
        ApplicationStatusChange(
            previous_status=ApplicationStatus.APPLIED,
            new_status=ApplicationStatus.SCREENING,
            changed_at=datetime(2026, 8, 5),
        ),
    )

    with pytest.raises(
        ValueError,
        match="status_history.changed_at must be timezone-aware",
    ):
        Application.restore(
            application_id=UUID(
                "12345678-1234-5678-1234-567812345678"
            ),
            company_name="OpenAI",
            job_title="Backend Engineer",
            status=ApplicationStatus.SCREENING,
            created_at=datetime(2026, 8, 1, tzinfo=UTC),
            status_history=status_history,
        )

def test_application_status_includes_accepted_value() -> None:
    status_values = {
        status.value
        for status in ApplicationStatus
    }

    assert "accepted" in status_values


@pytest.mark.parametrize(
    (
        "current_status",
        "new_status",
    ),
    [
        (
            ApplicationStatus.DRAFT,
            ApplicationStatus.INTERVIEW,
        ),
        (
            ApplicationStatus.SCREENING,
            ApplicationStatus.APPLIED,
        ),
        (
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.SCREENING,
        ),
        (
            ApplicationStatus.OFFER,
            ApplicationStatus.APPLIED,
        ),
    ],
)
def test_application_rejects_invalid_lifecycle_transition(
        current_status: ApplicationStatus,
        new_status: ApplicationStatus,
) -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=current_status,
    )

    with pytest.raises(
        ValueError,
        match=(
            f"cannot change status from "
            f"'{current_status.value}' to "
            f"'{new_status.value}'"
        ),
    ):
        application.change_status(new_status)

    assert application.status is current_status
    assert application.status_history == ()


@pytest.mark.parametrize(
    (
        "current_status",
        "new_status",
    ),
    [
        (
            ApplicationStatus.APPLIED,
            ApplicationStatus.INTERVIEW,
        ),
        (
            ApplicationStatus.SCREENING,
            ApplicationStatus.OFFER,
        ),
        (
            ApplicationStatus.OFFER,
            ApplicationStatus.ACCEPTED,
        ),
    ],
)
def test_application_allows_valid_lifecycle_transition(
        current_status: ApplicationStatus,
        new_status: ApplicationStatus,
) -> None:
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=current_status,
    )

    application.change_status(new_status)

    assert application.status is new_status
    assert len(application.status_history) == 1
    assert (
        application.status_history[0].previous_status
        is current_status
    )
    assert (
        application.status_history[0].new_status
        is new_status
    )
