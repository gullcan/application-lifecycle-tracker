from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4
from application_tracker.domain.validation import (
    require_timezone_aware,
)

class ApplicationStatus(Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

TERMINAL_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    }
)

@dataclass(frozen=True)
class ApplicationStatusChange:
    previous_status: ApplicationStatus
    new_status: ApplicationStatus
    changed_at: datetime


class Application:
    def __init__(
            self,
            company_name: str,
            job_title: str,
            status: ApplicationStatus = ApplicationStatus.DRAFT,
            follow_up_at: datetime | None = None,
    ) -> None:
        if not company_name.strip():
            raise ValueError("company_name cannot be blank")

        if not job_title.strip():
            raise ValueError("job_title cannot be blank")

        if not isinstance(status, ApplicationStatus):
            raise TypeError(
                "status must be an ApplicationStatus"
            )
        if follow_up_at is not None:
            require_timezone_aware(
                follow_up_at,
                "follow_up_at",
            )

        self.company_name = company_name
        self.job_title = job_title
        self._id: UUID = uuid4()
        self.created_at = datetime.now(UTC)

        self._status = status
        self._status_history: list[ApplicationStatusChange] = []
        self._follow_up_at = follow_up_at 

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def status(self) -> ApplicationStatus:
        return self._status

    @property
    def status_history(
        self,
    ) -> tuple[ApplicationStatusChange, ...]:
        return tuple(self._status_history)

    def change_status(
            self,
            new_status: ApplicationStatus,
    ) -> None:
        if not isinstance(new_status, ApplicationStatus):
            raise TypeError(
                "new_status must be an ApplicationStatus"
            )

        if self._status in TERMINAL_STATUSES:
            raise ValueError(
                f"cannot change status from terminal status "
                f"'{self._status.value}'"
            )

        if new_status is self._status:
            raise ValueError(
                "new status must be different from current status"
            )
        

        status_change = ApplicationStatusChange(
            previous_status=self._status,
            new_status=new_status,
            changed_at=datetime.now(UTC),
        )
        self._status = new_status
        self._status_history.append(status_change)

    def needs_follow_up(self, as_of: datetime) -> bool:
        require_timezone_aware(as_of, "as_of")

        if self._follow_up_at is None:
            return False
        
        if self._status in TERMINAL_STATUSES:
            return False
        
        return self._follow_up_at <= as_of

    @property
    def follow_up_at(self) -> datetime | None:
        return self._follow_up_at


    def schedule_follow_up(
            self,
            follow_up_at: datetime,
    ) -> None:
        require_timezone_aware(
            follow_up_at,
            "follow_up_at",
        )

        self._follow_up_at = follow_up_at

    def clear_follow_up(self) -> None:
        self._follow_up_at = None
