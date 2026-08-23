from pathlib import Path

from fastapi.testclient import TestClient

from application_tracker.bootstrap import build_app


def test_sqlite_backed_api_persists_across_app_instances(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "applications.db"

    writer = TestClient(
        build_app(database_path)
    )
    create_response = writer.post(
        "/applications",
        json={
            "company_name": "OpenAI",
            "job_title": "Backend Engineer",
            "status": "applied",
        },
    )

    assert create_response.status_code == 201

    application_id = create_response.json()["id"]

    reader = TestClient(
        build_app(database_path)
    )
    get_response = reader.get(
        f"/applications/{application_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == application_id
    assert get_response.json()["status"] == "applied"
