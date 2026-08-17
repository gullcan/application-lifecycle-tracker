from datetime import datetime

from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)

from application_tracker.repositories import (
    ApplicationRepository,
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
    ) -> Application:
        application = Application(
            company_name=company_name,
            job_title=job_title,
            status=status,
            follow_up_at=follow_up_at,
        )
        self._repository.add(application)

        return application 

    def change_application_status(
            self,
            application_id: UUID,  # Hangi Application’ın değiştirileceğini belirtir. UUID nesneleri immutable’dır; kimlik değeri oluşturulduktan sonra değişmez.
            new_status: ApplicationStatus,  # Hedef domain durumudur. Service raw string değil Enum beklediğini açıkça gösterir.
    ) -> Application:  #Başarılı işlemde güncellenmiş entity dönecektir.

        application = self._repository.get(application_id)  # Application bulma. Kayıt bulundu./Kayıt bulunamadı

        application.change_status(new_status) # Gerçek status kontrolünü yapar.

        return application