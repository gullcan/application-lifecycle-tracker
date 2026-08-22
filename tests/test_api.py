from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient

from application_tracker.api import create_app
from application_tracker.domain.models import (
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
