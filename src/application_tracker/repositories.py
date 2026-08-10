from uuid import UUID
from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)
from datetime import datetime
from application_tracker.domain.validation import (
    require_timezone_aware,
)

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
                
    def list_all(self) -> list[Application]:
        return list(self._applications.values())

    def find_by_status(
            self,
            status: ApplicationStatus,
    ) -> list[Application]:
        if not isinstance(status, ApplicationStatus):
            raise TypeError(
                "status must be an ApplicationStatus"
            )
        return [
            application
            for application in self._applications.values()
            if application.status is status
        ]

    def find_needing_follow_up(
            self,
            as_of: datetime,
    ) -> list[Application]:
        require_timezone_aware(as_of, "as_of")
        
        return [
            application #Sonuç listesine hangi değerin ekleneceği.
            for application in self._applications.values() #Verinin nereden geldiği.
            if application.needs_follow_up(as_of) #Hangi nesnelerin seçileceği.
        ]
                