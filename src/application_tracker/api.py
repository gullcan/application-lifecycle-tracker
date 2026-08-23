from datetime import datetime
from uuid import UUID
from csv import writer
from io import StringIO

from fastapi import FastAPI, HTTPException,Query, Request, Response, status

from fastapi.responses import JSONResponse

from application_tracker.domain.models import (
    Application,
    ApplicationSource,
    ApplicationStatus,
)
from application_tracker.repositories import (
    ApplicationNotFoundError,
    ApplicationRepository,
    ApplicationSort,
)
from application_tracker.services import ApplicationService

from typing import Annotated

from pydantic import (
    AwareDatetime,
    AnyHttpUrl,
    BaseModel,
    StringConstraints,
)

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

NonBlankString = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]
logger = logging.getLogger(__name__)

class ApplicationCreateRequest(BaseModel):
    company_name: NonBlankString
    job_title: NonBlankString
    status: ApplicationStatus = ApplicationStatus.DRAFT
    follow_up_at: AwareDatetime | None = None
    source: ApplicationSource | None = None
    job_url: AnyHttpUrl | None = None
    notes: Annotated[
        str,
        StringConstraints(max_length=5000),
    ] = ""


class ApplicationDetailsUpdateRequest(BaseModel):
    company_name: NonBlankString
    job_title: NonBlankString
    source: ApplicationSource | None = None
    job_url: AnyHttpUrl | None = None
    notes: Annotated[
        str,
        StringConstraints(max_length=5000),
    ] = ""

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
    source: ApplicationSource | None
    job_url: str | None
    notes: str
    archived_at: datetime | None
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
        source=application.source,
        job_url=application.job_url,
        notes=application.notes,
        archived_at=application.archived_at,
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
        version="1.1.0",
    )
    service = ApplicationService(repository)

    @app.middleware("http")
    async def log_http_request(
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            logger.exception(
                "HTTP request failed",
                extra={
                    "http_method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        logger.info(
            "HTTP request completed",
            extra={
                "http_method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response



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
            source=request.source,
            job_url=(
                str(request.job_url)
                if request.job_url is not None
                else None
            ),
            notes=request.notes,
        )

        return _to_response(application)


    @app.get(
        "/applications",
        response_model=list[ApplicationResponse],
    )
    def list_applications(
        status: ApplicationStatus | None = None,
        q: Annotated[
            str | None,
            Query(max_length=200),
        ] = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
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
            search=q,
            include_archived=include_archived,
            sort=sort,
            limit=limit,
            offset=offset,
        )

        return [
            _to_response(application)
            for application in applications
        ]

    @app.get(
        "/applications/export.csv",
        response_class=Response,
    )
    def export_applications(
        include_archived: bool = True,
    ) -> Response:
        applications = service.list_applications(
            include_archived=include_archived,
            sort=ApplicationSort.CREATED_DESC,
        )
        output = StringIO()
        csv_writer = writer(output)
        csv_writer.writerow(
            (
                "company_name",
                "job_title",
                "status",
                "source",
                "job_url",
                "notes",
                "follow_up_at",
                "created_at",
                "archived_at",
            )
        )
        for application in applications:
            csv_writer.writerow(
                (
                    application.company_name,
                    application.job_title,
                    application.status.value,
                    (
                        application.source.value
                        if application.source is not None
                        else ""
                    ),
                    application.job_url or "",
                    application.notes,
                    (
                        application.follow_up_at.isoformat()
                        if application.follow_up_at is not None
                        else ""
                    ),
                    application.created_at.isoformat(),
                    (
                        application.archived_at.isoformat()
                        if application.archived_at is not None
                        else ""
                    ),
                )
            )

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    "attachment; filename=applications.csv"
                ),
            },
        )

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
        "/applications/{application_id}",
        response_model=ApplicationResponse,
    )
    def update_application_details(
        application_id: UUID,
        request: ApplicationDetailsUpdateRequest,
    ) -> ApplicationResponse:
        application = service.update_application_details(
            application_id,
            company_name=request.company_name,
            job_title=request.job_title,
            source=request.source,
            job_url=(
                str(request.job_url)
                if request.job_url is not None
                else None
            ),
            notes=request.notes,
        )

        return _to_response(application)

    @app.put(
        "/applications/{application_id}/archive",
        response_model=ApplicationResponse,
    )
    def archive_application(
        application_id: UUID,
    ) -> ApplicationResponse:
        try:
            application = service.archive_application(
                application_id
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error

        return _to_response(application)

    @app.delete(
        "/applications/{application_id}/archive",
        response_model=ApplicationResponse,
    )
    def restore_archived_application(
        application_id: UUID,
    ) -> ApplicationResponse:
        try:
            application = (
                service.restore_archived_application(
                    application_id
                )
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error

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
                status_code=status.HTTP_409_CONFLICT,
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
