from uuid import UUID
from application_tracker.domain.models import Application

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
                


                