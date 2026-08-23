from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, HTTPException,Query, Request, status

from fastapi.responses import JSONResponse

from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)
from application_tracker.repositories import (
    ApplicationNotFoundError,
    ApplicationRepository,
)
from application_tracker.services import ApplicationService

from typing import Annotated

from pydantic import (
    AwareDatetime,
    BaseModel,
    StringConstraints,
)

NonBlankString = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]

class ApplicationCreateRequest(BaseModel):
    company_name: NonBlankString
    job_title: NonBlankString
    status: ApplicationStatus = ApplicationStatus.DRAFT
    follow_up_at: AwareDatetime | None = None

class ApplicationStatusChangeResponse(BaseModel):
    previous_status: ApplicationStatus
    new_status: ApplicationStatus
    changed_at: datetime

class ApplicationStatusUpdateRequest(BaseModel):
    status: ApplicationStatus

class ApplicationResponse(BaseModel):
    id: UUID
    company_name: str
    job_title: str
    status: ApplicationStatus
    created_at: datetime
    follow_up_at: datetime | None
    status_history: list[ApplicationStatusChangeResponse]

class FollowUpScheduleRequest(BaseModel):
    follow_up_at: AwareDatetime

class HealthResponse(BaseModel):
    status: str

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
        status_history=[
            ApplicationStatusChangeResponse(
                previous_status=change.previous_status,
                new_status=change.new_status,
                changed_at=change.changed_at,
            )
            for change in application.status_history
        ],
        
    )


def create_app(
        repository: ApplicationRepository,
) -> FastAPI:
    app = FastAPI(
        title="Application Lifecycle Tracker",
        version="0.1.0",
    )
    service = ApplicationService(repository)

    @app.exception_handler(
        ApplicationNotFoundError
    )
    async def application_not_found_handler(
        _request: Request,
        error: ApplicationNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(error),
            },
        )

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
        limit: Annotated[
            int,
            Query(ge=1, le=100),
        ] = 50,
        offset: Annotated[
            int,
            Query(ge=0),
        ] = 0,
    ) -> list[ApplicationResponse]:
        applications = service.list_applications(
            status=status,
            limit=limit,
            offset=offset,
        )

        return [
            _to_response(application)
            for application in applications
        ]

    @app.get(
        "/applications/follow-ups",
        response_model=list[ApplicationResponse],
    )
    def list_applications_needing_follow_up(
        as_of: AwareDatetime,
    ) -> list[ApplicationResponse]:
        applications = (
            service.list_applications_needing_follow_up(
                as_of=as_of,
            )
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
        application = service.get_application(
            application_id
        )

        return _to_response(application)

    @app.patch(
        "/applications/{application_id}/status",
        response_model=ApplicationResponse,
    )
    def change_application_status(
            application_id: UUID,
            request: ApplicationStatusUpdateRequest,
    ) -> ApplicationResponse:
        try:
            application = service.change_application_status(
                application_id=application_id,
                new_status=request.status,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error

        return _to_response(application)

    @app.put(
        "/applications/{application_id}/follow-up",
        response_model=ApplicationResponse,
    )
    def schedule_application_follow_up(
            application_id: UUID,
            request: FollowUpScheduleRequest,
    ) -> ApplicationResponse:
        try:
            application = (
                service.schedule_application_follow_up(
                    application_id=application_id,
                    follow_up_at=request.follow_up_at,
                )
            )
        except ApplicationNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=str(error),
            ) from error

        return _to_response(application)

    @app.delete(
        "/applications/{application_id}/follow-up",
        response_model=ApplicationResponse,
    )
    def clear_application_follow_up(
        application_id: UUID,
    ) -> ApplicationResponse:
        application = (
            service.clear_application_follow_up(
                application_id=application_id,
            )
        )

        return _to_response(application)

    @app.get(
        "/health",
        response_model=HealthResponse,
    )
    def health() -> HealthResponse:
        return HealthResponse(status="ok")
    
    return app

