from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from application_tracker.api import create_app
from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)

from application_tracker.repositories import (
    InMemoryApplicationRepository,
)


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
        response.json()["detail"]
        == "follow_up_at must be timezone-aware"
    )
    assert repository.get(
        application.id
    ).follow_up_at is None