from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

class ApplicationStatus(Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrwan"

TERMINAL_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    }
)

@dataclass
class Application:
    company_name: str
    job_title: str
    status: ApplicationStatus = ApplicationStatus.DRAFT
    id: UUID = field(default_factory=uuid4, init=False)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
        init=False,
    )

#Burada nesnenin oluşturulma kurallarını koruyoruz.Nesnenin boş şirket veya pozisyon bilgisiyle oluşturulmasını engelliyoruz.
    def __post_init__(self) -> None:
        if not self.company_name.strip():
            raise ValueError("company_name cannot be blank")

        if not self.job_title.strip():
            raise ValueError("job_title cannot be blank")

        if not isinstance(self.status, ApplicationStatus):
            raise TypeError("status must be an ApplicationStatus")


    def change_status(self, new_status: ApplicationStatus) -> None:
        if not isinstance(new_status, ApplicationStatus):
            raise TypeError("new_status must be an ApplicationStatus")

        if self.status in TERMINAL_STATUSES:
            raise ValueError(
                f"cannot change status from terminal status"
                f"'{self.status.value}'"
            )
        
        if new_status is self.status:
            raise ValueError(
                "new status must be different from current status"
            )
        
        self.status = new_status