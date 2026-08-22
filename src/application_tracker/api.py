from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, status
from pydantic import BaseModel

from application_tracker.domain.models import (
    ApplicationStatus,
)
from application_tracker.repositories import (
    ApplicationRepository,
)
from application_tracker.services import ApplicationService


class ApplicationCreateRequest(BaseModel):
    company_name: str
    job_title: str
    status: ApplicationStatus = ApplicationStatus.DRAFT
    follow_up_at: datetime | None = None


class ApplicationResponse(BaseModel):
    id: UUID
    company_name: str
    job_title: str
    status: ApplicationStatus
    created_at: datetime
    follow_up_at: datetime | None


def create_app(
        repository: ApplicationRepository,
) -> FastAPI:
    app = FastAPI(
        title="Application Lifecycle Tracker",
        version="0.1.0",
    )
    service = ApplicationService(repository)

    @app.post(
        "/applications",
        response_model=ApplicationResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_application(
        request: ApplicationCreateRequest,
    ) -> ApplicationResponse:
        application = service.create_application(
            company_name=request.company_name,
            job_title=request.job_title,
            status=request.status,
            follow_up_at=request.follow_up_at,
        )

        return ApplicationResponse(
            id=application.id,
            company_name=application.company_name,
            job_title=application.job_title,
            status=application.status,
            created_at=application.created_at,
            follow_up_at=application.follow_up_at,
        )
    return app
