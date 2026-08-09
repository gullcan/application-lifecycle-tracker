from dataclasses import dataclass
from enum import Enum

class ApplicationStatus(Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrwan"

@dataclass
class Application:
    company_name: str
    job_title: str
    status: ApplicationStatus = ApplicationStatus.DRAFT

#Burada nesnenin oluşturulma kurallarını koruyoruz.
    def __post_init__(self) -> None:
        if not self.company_name.strip():
            raise ValueError("company_name cannot be blank")

        if not self.job_title.strip():
            raise ValueError("job_title cannot be blank")

        if not isinstance(self.status, ApplicationStatus):
            raise TypeError("status must be an ApplicationStatus")