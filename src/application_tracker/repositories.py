from uuid import UUID
from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)
from datetime import datetime
from application_tracker.domain.validation import (
    require_timezone_aware,
)
from typing import Protocol
from enum import Enum
from collections.abc import Iterable


class ApplicationSort(Enum):
    CREATED_ASC = "created_asc"
    CREATED_DESC = "created_desc"
    COMPANY_ASC = "company_asc"

class ApplicationRepository(Protocol):
    def add(self, application: Application) -> None:
        ...     # Burada methodun implementation’ını yazmıyoruz; yalnızca kontratını tarif ediyoruz

    def get(
            self,
            application_id: UUID,
    ) -> Application:
        ...      # Bu repository bir UUID almalı ve bir Application döndürmeli.

    def list_all(
        self,
        *,
        search: str | None = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Application]:
        ...

    def find_by_status(
        self,
        status: ApplicationStatus,
        *,
        search: str | None = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Application]:
        ...

    def find_needing_follow_up(
            self,
            as_of: datetime,
    ) -> list[Application]:
        ...

    def save(self, application: Application) -> None: # Var olan bir Application’ın güncel durumunu sakla. Kayıt yoksa hata üret.
        ...

class ApplicationNotFoundError(LookupError):
    """Raised when an application cannot be found."""

class DuplicateApplicationError(ValueError):
    """Raised when an application is added more than once."""

class InMemoryApplicationRepository:
    def __init__(self) -> None:
        self._applications: dict[UUID, Application] = {}

    def add(self, application: Application) -> None:
        if application.id in self._applications:
            raise DuplicateApplicationError(
                f"application with id '{application.id}' already exists"
            )
        self._applications[application.id] = application

    def get(self, application_id: UUID) -> Application:
        try:
            return self._applications[application_id]
        except KeyError:
            raise ApplicationNotFoundError(
                f"application with id'{application_id}' was not found"
            ) from None

    def list_all(
        self,
        *,
        search: str | None = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Application]:
        applications = self._filter_and_sort(
            self._applications.values(),
            search=search,
            include_archived=include_archived,
            sort=sort,
        )

        if limit is None:
            return applications[offset:]

        return applications[
            offset:offset + limit
        ]

    def find_by_status(
        self,
        status: ApplicationStatus,
        *,
        search: str | None = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Application]:
        if not isinstance(status, ApplicationStatus):
            raise TypeError(
                "status must be an ApplicationStatus"
            )

        applications = self._filter_and_sort(
            (
                application
                for application
                in self._applications.values()
                if application.status is status
            ),
            search=search,
            include_archived=include_archived,
            sort=sort,
        )

        if limit is None:
            return applications[offset:]

        return applications[
            offset:offset + limit
        ]

    def _filter_and_sort(
        self,
        applications: Iterable[Application],
        *,
        search: str | None,
        include_archived: bool,
        sort: ApplicationSort,
    ) -> list[Application]:
        if not isinstance(sort, ApplicationSort):
            raise TypeError("sort must be an ApplicationSort")

        normalized_search = (
            search.strip().casefold()
            if search is not None
            else ""
        )
        filtered = [
            application
            for application in applications
            if (
                include_archived
                or not application.is_archived
            )
            and (
                not normalized_search
                or normalized_search in " ".join(
                    (
                        application.company_name,
                        application.job_title,
                        application.notes,
                        (
                            application.source.value
                            if application.source is not None
                            else ""
                        ),
                    )
                ).casefold()
            )
        ]

        if sort is ApplicationSort.COMPANY_ASC:
            return sorted(
                filtered,
                key=lambda application: (
                    application.company_name.casefold(),
                    application.created_at,
                    str(application.id),
                ),
            )

        return sorted(
            filtered,
            key=lambda application: (
                application.created_at,
                str(application.id),
            ),
            reverse=sort is ApplicationSort.CREATED_DESC,
        )

    def find_needing_follow_up(
            self,
            as_of: datetime,
    ) -> list[Application]:
        require_timezone_aware(as_of, "as_of")

        return [
            application # Sonuç listesine hangi değerin ekleneceği.
            for application in self._applications.values() # Verinin nereden geldiği.
            if application.needs_follow_up(as_of) # Hangi nesnelerin seçileceği.
        ]


    def save(self, application: Application) -> None:
        if application.id not in self._applications:
            raise ApplicationNotFoundError(
                f"application with id "
                f"'{application.id}' was not found"
            )
        self._applications[application.id] = application
