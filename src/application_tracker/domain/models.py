from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4
from application_tracker.domain.validation import (
    require_timezone_aware,
)
from typing import Self

class ApplicationStatus(Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationSource(Enum):
    LINKEDIN = "linkedin"
    COMPANY_WEBSITE = "company_website"
    REFERRAL = "referral"
    EMAIL = "email"
    OTHER = "other"

TERMINAL_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.ACCEPTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    }
)
ALLOWED_STATUS_TRANSITIONS: dict[
    ApplicationStatus,
    frozenset[ApplicationStatus],
] = {
    ApplicationStatus.DRAFT: frozenset(
        {
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.APPLIED: frozenset(
        {
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.SCREENING: frozenset(
        {
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.INTERVIEW: frozenset(
        {
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.OFFER: frozenset(
        {
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.ACCEPTED: frozenset(),
    ApplicationStatus.REJECTED: frozenset(),
    ApplicationStatus.WITHDRAWN: frozenset(),
}

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
            source: ApplicationSource | None = None,
            job_url: str | None = None,
            notes: str = "",
    ) -> None:
        if not company_name.strip():
            raise ValueError("company_name cannot be blank")

        if not job_title.strip():
            raise ValueError("job_title cannot be blank")

        if not isinstance(status, ApplicationStatus):
            raise TypeError(
                "status must be an ApplicationStatus"
            )
        if source is not None and not isinstance(
            source,
            ApplicationSource,
        ):
            raise TypeError(
                "source must be an ApplicationSource"
            )
        if job_url is not None and not job_url.strip():
            raise ValueError("job_url cannot be blank")
        if follow_up_at is not None:
            require_timezone_aware(
                follow_up_at,
                "follow_up_at",
            )

        self.company_name = company_name.strip()
        self.job_title = job_title.strip()
        self.source = source
        self.job_url = (
            job_url.strip()
            if job_url is not None
            else None
        )
        self.notes = notes.strip()
        self._id: UUID = uuid4()
        self.created_at = datetime.now(UTC)

        self._status = status
        self._status_history: list[ApplicationStatusChange] = []
        self._follow_up_at = follow_up_at
        self._archived_at: datetime | None = None

    @classmethod
    def restore( # restore() is a factory method.
        cls,
        *,
        application_id: UUID,
        company_name: str,
        job_title: str,
        status: ApplicationStatus,
        created_at: datetime,
        follow_up_at: datetime | None = None,
        source: ApplicationSource | None = None,
        job_url: str | None = None,
        notes: str = "",
        archived_at: datetime | None = None,
        status_history: tuple [
            ApplicationStatusChange,
            ...
        ] = (),

    ) -> Self:
        require_timezone_aware(
            created_at,
            "created_at",
        )
        for status_change in status_history:
            require_timezone_aware(
                status_change.changed_at,
                "status_history.changed_at",
            )
        if archived_at is not None:
            require_timezone_aware(
                archived_at,
                "archived_at",
            )

        application = cls(
            company_name=company_name,
            job_title=job_title,
            status=status,
            follow_up_at=follow_up_at,
            source=source,
            job_url=job_url,
            notes=notes,
        )

        application._id= application_id
        application.created_at = created_at
        application._status_history = list(status_history)
        application._archived_at = archived_at

        return application


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

    @property
    def archived_at(self) -> datetime | None:
        return self._archived_at

    @property
    def is_archived(self) -> bool:
        return self._archived_at is not None

    def update_details(
        self,
        *,
        company_name: str,
        job_title: str,
        source: ApplicationSource | None,
        job_url: str | None,
        notes: str,
    ) -> None:
        if not company_name.strip():
            raise ValueError("company_name cannot be blank")
        if not job_title.strip():
            raise ValueError("job_title cannot be blank")
        if source is not None and not isinstance(
            source,
            ApplicationSource,
        ):
            raise TypeError(
                "source must be an ApplicationSource"
            )
        if job_url is not None and not job_url.strip():
            raise ValueError("job_url cannot be blank")

        self.company_name = company_name.strip()
        self.job_title = job_title.strip()
        self.source = source
        self.job_url = (
            job_url.strip()
            if job_url is not None
            else None
        )
        self.notes = notes.strip()

    def archive(self) -> None:
        if self._archived_at is not None:
            raise ValueError("application is already archived")

        self._archived_at = datetime.now(UTC)

    def restore_from_archive(self) -> None:
        if self._archived_at is None:
            raise ValueError("application is not archived")

        self._archived_at = None

    def change_status(
            self,
            new_status: ApplicationStatus,
    ) -> None:
        if not isinstance(new_status, ApplicationStatus):
            raise TypeError(
                "new_status must be an ApplicationStatus"
            )

        if self.is_archived:
            raise ValueError(
                "cannot change status of archived application"
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

        allowed_transitions = (
            ALLOWED_STATUS_TRANSITIONS[self._status]
        )

        if new_status not in allowed_transitions:
            raise ValueError(
                f"cannot change status from "
                f"'{self._status.value}' to "
                f"'{new_status.value}'"
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

        if self.is_archived:
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
        if self.is_archived:
            raise ValueError(
                "cannot schedule follow-up for archived application"
            )

        require_timezone_aware(
            follow_up_at,
            "follow_up_at",
        )

        self._follow_up_at = follow_up_at

    def clear_follow_up(self) -> None:
        self._follow_up_at = None
