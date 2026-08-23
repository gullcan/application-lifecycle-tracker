from datetime import UTC, datetime

from application_tracker.domain.models import (
    Application,
    ApplicationStatus,
)
from application_tracker.repositories import(
    InMemoryApplicationRepository,
)
from application_tracker.services import ApplicationService


def _format_application(
        application: Application,
) -> str:
    return (
        f"{application.company_name}"
        f" | {application.job_title}"
        f" | {application.status.value}"
    )


def main() -> None:
    repository = InMemoryApplicationRepository()
    service = ApplicationService(repository)

    as_of = datetime(
        2026,
        8,
        20,
        tzinfo=UTC,
    )

    openai_application = service.create_application(
        company_name="OpenAI",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        follow_up_at=datetime(
            2026,
            8,
            19,
            tzinfo=UTC,
        ),
    )
    service.change_application_status(
        application_id=openai_application.id,
        new_status=ApplicationStatus.SCREENING,
    )

    service.create_application(
        company_name="Anthropic",
        job_title="Python Engineer",
        status=ApplicationStatus.INTERVIEW,
        follow_up_at=datetime(
            2026,
            8,
            21,
            tzinfo=UTC,
        ),
    )

    service.create_application(
        company_name="GitHub",
        job_title="Platform Engineer",
        status=ApplicationStatus.REJECTED,
        follow_up_at=datetime(
            2026,
            8,
            18,
            tzinfo=UTC,
        ),
    )

    all_applications = service.list_applications()
    applications_needing_follow_up = (
        service.list_applications_needing_follow_up(
            as_of=as_of,
        )
    )

    print(
        f"All applications: {len(all_applications)}"
    )
    print(
        f"Needs follow-up as of {as_of.isoformat()}:"
    )

    for application in applications_needing_follow_up:
        print(f"- {_format_application(application)}")

if __name__ == "__main__":
    main()



