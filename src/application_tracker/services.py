from datetime import datetime

from application_tracker.domain.models import (
    Application,
    ApplicationSource,
    ApplicationStatus,
)

from application_tracker.repositories import (
    ApplicationRepository,
    ApplicationSort,
)
from uuid import UUID

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
        source: ApplicationSource | None = None,
        job_url: str | None = None,
        notes: str = "",
    ) -> Application:
        application = Application(
            company_name=company_name,
            job_title=job_title,
            status=status,
            follow_up_at=follow_up_at,
            source=source,
            job_url=job_url,
            notes=notes,
        )
        self._repository.add(application)

        return application

    def update_application_details(
        self,
        application_id: UUID,
        *,
        company_name: str,
        job_title: str,
        source: ApplicationSource | None,
        job_url: str | None,
        notes: str,
    ) -> Application:
        application = self._repository.get(application_id)
        application.update_details(
            company_name=company_name,
            job_title=job_title,
            source=source,
            job_url=job_url,
            notes=notes,
        )
        self._repository.save(application)

        return application

    def archive_application(
        self,
        application_id: UUID,
    ) -> Application:
        application = self._repository.get(application_id)
        application.archive()
        self._repository.save(application)

        return application

    def restore_archived_application(
        self,
        application_id: UUID,
    ) -> Application:
        application = self._repository.get(application_id)
        application.restore_from_archive()
        self._repository.save(application)

        return application

    def change_application_status(
            self,
            application_id: UUID,  # Hangi Application’ın değiştirileceğini belirtir. UUID nesneleri immutable’dır; kimlik değeri oluşturulduktan sonra değişmez.
            new_status: ApplicationStatus,  # Hedef domain durumudur. Service raw string değil Enum beklediğini açıkça gösterir.
    ) -> Application:  # Başarılı işlemde güncellenmiş entity dönecektir.

        application = self._repository.get(application_id)  # Application bulma. Kayıt bulundu./Kayıt bulunamadı

        application.change_status(new_status) # Gerçek status kontrolünü yapar.

        self._repository.save(application)

        return application

    def schedule_application_follow_up(
            self,
            application_id:UUID,
            follow_up_at: datetime,
    ) -> Application:
        application = self._repository.get(application_id)

        application.schedule_follow_up(follow_up_at)

        self._repository.save(application)

        return application

    def clear_application_follow_up(
            self,
            application_id: UUID,
    ) -> Application:
        application = self._repository.get(application_id)

        application.clear_follow_up()

        self._repository.save(application)

        return application


    def list_applications(
        self,
        status: ApplicationStatus | None = None,
        *,
        search: str | None = None,
        include_archived: bool = False,
        sort: ApplicationSort = ApplicationSort.CREATED_ASC,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Application]:
        if status is None:
            return self._repository.list_all(
                limit=limit,
                offset=offset,
                search=search,
                include_archived=include_archived,
                sort=sort,
            )

        return self._repository.find_by_status(
            status,
            limit=limit,
            offset=offset,
            search=search,
            include_archived=include_archived,
            sort=sort,
        )


    def list_applications_needing_follow_up(
            self,
            as_of: datetime,
    ) -> list[Application]:
        return self._repository.find_needing_follow_up(
            as_of
        )

    def get_application(
            self,
            application_id: UUID,
    ) -> Application:
        return self._repository.get(application_id)
