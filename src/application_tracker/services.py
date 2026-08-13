from datetime import datetime

from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)

from application_tracker.repositories import (
    ApplicationRepository,
)

class ApplicationService:
    def __init__(
        self,
        repository: ApplicationRepository,
    ) -> None:
        self._repository = repository


    def create_application(
        self,
        company_name: str,
        job_title: str,
        status: ApplicationStatus = ApplicationStatus.DRAFT,
        follow_up_at: datetime | None = None,
    ) -> Application:
        application = Application(
            company_name=company_name,
            job_title=job_title,
            status=status,
            follow_up_at=follow_up_at,
        )
        self._repository.add(application)

        return application 

    