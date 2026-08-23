from datetime import UTC, datetime
from uuid import UUID, uuid4

import logging

from fastapi.testclient import TestClient

from application_tracker.api import create_app
from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)

from application_tracker.repositories import (
    InMemoryApplicationRepository,
)
import pytest

@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("company_name", "   "),
        ("job_title", "   "),
    ],
)
def test_create_application_rejects_blank_required_field(
    field_name: str,
    field_value: str,
) -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))
    request_body = {
        "company_name": "OpenAI",
        "job_title": "Backend Engineer",
    }
    request_body[field_name] = field_value

    response = client.post(
        "/applications",
        json=request_body,
    )

    assert response.status_code == 422
    assert repository.list_all() == []


def test_create_application_rejects_naive_follow_up_datetime(
) -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))

    response = client.post(
        "/applications",
        json={
            "company_name": "OpenAI",
            "job_title": "Backend Engineer",
            "follow_up_at": "2026-08-25T09:00:00",
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["loc"]
        == ["body", "follow_up_at"]
    )
    assert repository.list_all() == []


def test_create_application_returns_created_application() -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))

    response = client.post(
        "/applications",
        json={
            "company_name": "OpenAI",
            "job_title": "Backend Engineer",
            "status": "applied",
            "follow_up_at": "2026-08-25T09:00:00+00:00",
        },
    )

    assert response.status_code == 201

    body = response.json()
    application_id = UUID(body["id"])

    assert body["company_name"] == "OpenAI"
    assert body["job_title"] == "Backend Engineer"
    assert body["status"] == "applied"
    assert datetime.fromisoformat(
        body["follow_up_at"]
    ) == datetime.fromisoformat(
        "2026-08-25T09:00:00+00:00"
    )
    assert datetime.fromisoformat(
        body["created_at"]
    ).tzinfo is not None

    stored = repository.get(application_id)

    assert stored.status is ApplicationStatus.APPLIED
    assert stored.company_name == "OpenAI"


def test_get_application_returns_application() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.SCREENING,
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.get(
        f"/applications/{application.id}"
    )

    assert response.status_code == 200
    assert response.json() ["id"] == str(application.id)
    assert response.json() ["company_name"] == "OpenAI"
    assert response.json() ["status"] == "screening"


def test_get_application_returns_404_for_unknown_id() -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))
    unknown_id = uuid4()

    response = client.get(
        f"/applications/{unknown_id}"
    )

    assert response.status_code == 404
    assert str(unknown_id) in response.json() ["detail"]


def test_get_application_rejects_invalid_uuid() -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))

    response = client.get(
        "/applications/not-a-valid-uuid"
    )

    assert response.status_code == 422


def test_list_applications_support_status_filter() -> None:
    repository = InMemoryApplicationRepository()
    applied = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    interview = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
    )
    repository.add(applied)
    repository.add(interview)
    client = TestClient(create_app(repository))

    all_response = client.get("/applications")
    filtered_response= client.get(
        "/applications",
        params={"status": "interview"},
    )

    assert all_response.status_code == 200
    assert{
        item["id"]
        for item in all_response.json()
    } == {
        str(applied.id),
        str(interview.id),
    }

    assert filtered_response.status_code == 200
    assert [
        item["id"]
        for item in filtered_response.json()
    ] == [str(interview.id)]


def test_change_status_returns_updated_application() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.patch(
        f"/applications/{application.id}/status",
        json={"status": "screening"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "screening"
    assert body["status_history"] == [
        {
            "previous_status": "applied",
            "new_status": "screening",
            "changed_at": body["status_history"][0]["changed_at"],
        }
    ]

    stored = repository.get(application.id)

    assert stored.status is ApplicationStatus.SCREENING
    assert len(stored.status_history) == 1


def test_change_status_returns_404_for_unknown_application() -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))
    unknown_id = uuid4()

    response = client.patch(
        f"/applications/{unknown_id}/status",
        json={"status": "screening"},
    )

    assert response.status_code == 404
    assert str(unknown_id) in response.json()["detail"]


def test_change_status_returns_409_for_invalid_transition() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.patch(
        f"/applications/{application.id}/status",
        json={"status": "applied"},
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "new status must be different from current status"
    )


def test_change_status_rejects_unknown_status() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.patch(
        f"/applications/{application.id}/status",
        json={"status": "hired"},
    )

    assert response.status_code == 422
    assert repository.get(
        application.id
    ).status is ApplicationStatus.DRAFT

def test_schedule_follow_up_returns_updated_application() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    repository.add(application)
    client = TestClient(create_app(repository))
    follow_up_at = datetime.fromisoformat(
        "2026-08-25T09:00:00+00:00"
    )

    response = client.put(
        f"/applications/{application.id}/follow-up",
        json={
            "follow_up_at": follow_up_at.isoformat(),
        },
    )

    assert response.status_code == 200
    assert datetime.fromisoformat(
        response.json()["follow_up_at"]
    ) == follow_up_at
    assert repository.get(
        application.id
    ).follow_up_at == follow_up_at


def test_clear_follow_up_returns_updated_application() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        follow_up_at=datetime.fromisoformat(
            "2026-08-25T09:00:00+00:00"
        ),
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.delete(
        f"/applications/{application.id}/follow-up"
    )

    assert response.status_code == 200
    assert response.json()["follow_up_at"] is None
    assert repository.get(
        application.id
    ).follow_up_at is None


def test_schedule_follow_up_returns_404_for_unknown_application() -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))
    unknown_id = uuid4()

    response = client.put(
        f"/applications/{unknown_id}/follow-up",
        json={
            "follow_up_at": "2026-08-25T09:00:00+00:00",
        },
    )

    assert response.status_code == 404
    assert str(unknown_id) in response.json()["detail"]


def test_clear_follow_up_returns_404_for_unknown_application() -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))
    unknown_id = uuid4()

    response = client.delete(
        f"/applications/{unknown_id}/follow-up"
    )

    assert response.status_code == 404
    assert str(unknown_id) in response.json()["detail"]


def test_schedule_follow_up_rejects_naive_datetime() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.put(
        f"/applications/{application.id}/follow-up",
        json={
            "follow_up_at": "2026-08-25T09:00:00",
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["loc"]
        == ["body", "follow_up_at"]
    )
    assert repository.get(
        application.id
    ).follow_up_at is None

def test_health_returns_ok() -> None:
    client = TestClient(
        create_app(
            InMemoryApplicationRepository()
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_list_applications_needing_follow_up(
) -> None:
    repository = InMemoryApplicationRepository()
    as_of = datetime(
        2026,
        8,
        25,
        9,
        tzinfo=UTC,
    )

    due_application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.SCREENING,
        follow_up_at=datetime(
            2026,
            8,
            24,
            9,
            tzinfo=UTC,
        ),
    )
    future_application = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
        follow_up_at=datetime(
            2026,
            8,
            26,
            9,
            tzinfo=UTC,
        ),
    )
    terminal_application = Application(
        company_name="GitHub",
        job_title="Platform Engineer",
        status=ApplicationStatus.REJECTED,
        follow_up_at=datetime(
            2026,
            8,
            23,
            9,
            tzinfo=UTC,
        ),
    )

    repository.add(due_application)
    repository.add(future_application)
    repository.add(terminal_application)
    client = TestClient(create_app(repository))

    response = client.get(
        "/applications/follow-ups",
        params={
            "as_of": as_of.isoformat(),
        },
    )

    assert response.status_code == 200, response.json()
    assert [
        item["id"]
        for item in response.json()
    ] == [str(due_application.id)]


def test_follow_up_query_rejects_naive_as_of(
) -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))

    response = client.get(
        "/applications/follow-ups",
        params={
            "as_of": "2026-08-25T09:00:00",
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["loc"]
        == ["query", "as_of"]
    )


def test_list_applications_supports_pagination(
) -> None:
    repository = InMemoryApplicationRepository()
    applications = [
        Application(
            company_name="OpenAI",
            job_title="Backend Engineer",
        ),
        Application(
            company_name="Anthropic",
            job_title="Python Engineer",
        ),
        Application(
            company_name="GitHub",
            job_title="Platform Engineer",
        ),
    ]

    for application in applications:
        repository.add(application)

    client = TestClient(create_app(repository))

    response = client.get(
        "/applications",
        params={
            "limit": 2,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    assert [
        item["id"]
        for item in response.json()
    ] == [
        str(application.id)
        for application in applications[1:3]
    ]

def test_list_applications_combines_status_and_pagination(
) -> None:
    repository = InMemoryApplicationRepository()
    first_applied = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )
    interview = Application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
    )
    second_applied = Application(
        company_name="GitHub",
        job_title="Platform Engineer",
        status=ApplicationStatus.APPLIED,
    )

    repository.add(first_applied)
    repository.add(interview)
    repository.add(second_applied)
    client = TestClient(create_app(repository))

    response = client.get(
        "/applications",
        params={
            "status": "applied",
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    assert [
        item["id"]
        for item in response.json()
    ] == [str(second_applied.id)]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
def test_list_applications_rejects_invalid_pagination(
    params: dict[str, int],
) -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))

    response = client.get(
        "/applications",
        params=params,
    )

    assert response.status_code == 422

def test_health_request_records_log_context(
        caplog: pytest.LogCaptureFixture,
) -> None:
    repository = InMemoryApplicationRepository()
    client = TestClient(create_app(repository))

    with caplog.at_level(
        logging.INFO,
        logger="application_tracker.api",
    ):
        response = client.get("/health")

    request_records = [
        record
        for record in caplog.records
        if record.getMessage()
        == "HTTP request completed"
    ]

    assert response.status_code == 200
    assert len(request_records) == 1

    record = request_records[0]

    assert record.http_method == "GET"
    assert record.path == "/health"
    assert record.status_code == 200
    assert record.duration_ms >= 0

def test_unhandled_error_records_log_context(
        caplog: pytest.LogCaptureFixture,
) -> None:
    repository = InMemoryApplicationRepository()
    app = create_app(repository)

    @app.get("/test/failure")
    def fail() -> None:
        raise RuntimeError("unexpected failure")

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    with caplog.at_level(
        logging.ERROR,
        logger="application_tracker.api",
    ):
        response = client.get("/test/failure")

    failure_records = [
        record
        for record in caplog.records
        if record.getMessage()
        == "HTTP request failed"
    ]

    assert response.status_code == 500
    assert len(failure_records) == 1

    record = failure_records[0]

    assert record.http_method == "GET"
    assert record.path == "/test/failure"
    assert record.status_code == 500
    assert record.duration_ms >= 0
    assert record.exc_info is not None

def test_change_status_accepts_application_offer() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.OFFER,
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.patch(
        f"/applications/{application.id}/status",
        json={
            "status": "accepted",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["status_history"][-1][
        "previous_status"
    ] == "offer"
    assert response.json()["status_history"][-1][
        "new_status"
    ] == "accepted"


def test_change_status_rejects_backward_transition() -> None:
    repository = InMemoryApplicationRepository()
    application = Application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.INTERVIEW,
    )
    repository.add(application)
    client = TestClient(create_app(repository))

    response = client.patch(
        f"/applications/{application.id}/status",
        json={
            "status": "applied",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == (
            "cannot change status from "
            "'interview' to 'applied'"
        )
    )
    assert application.status is ApplicationStatus.INTERVIEW
    assert application.status_history == ()
