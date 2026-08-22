from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)
from application_tracker.repositories import (
    ApplicationNotFoundError,
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


def _to_response(
        application: Application,
) -> ApplicationResponse:
    return ApplicationResponse(
        id=application.id,
        company_name=application.company_name,
        job_title=application.job_title,
        status=application.status,
        created_at=application.created_at,
        follow_up_at=application.follow_up_at,
    )


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

        return _to_response(application)


    @app.get(
        "/applications",
        response_model=list[ApplicationResponse],
    )
    def list_applications(
        status: ApplicationStatus | None = None,
    ) -> list[ApplicationResponse]:
        applications = service.list_applications(
            status=status
        )
        return [
            _to_response(application)
            for application in applications
        ]

    @app.get(
        "/applications/{application_id}",
        response_model=ApplicationResponse,
    )
    def get_applications(
        application_id: UUID,
    ) -> ApplicationResponse:
        try: 
            application = service.get_application(
                application_id
            )
        except ApplicationNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

        return _to_response(application)
    
    return app

