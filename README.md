# Application Lifecycle Tracker

A pure-Python backend core for tracking job applications, lifecycle transitions, status history, and follow-up schedules.

## Problem

Job seekers often manage applications across multiple platforms, emails, referrals, and company portals. As the number of applications grows, it becomes difficult to answer questions such as:

- Which applications are still active?
- What stage is each application in?
- How did an application reach its current status?
- Which applications require follow-up today?
- Which applications are already closed?

Application Lifecycle Tracker models this workflow as explicit domain rules instead of treating applications as simple CRUD records.

## Current milestone

The first milestone implements the core business logic using pure Python.

Current capabilities include:

- Creating job applications with validated company and job-title values
- Representing lifecycle states with an enum
- Enforcing valid status transitions
- Preventing changes to terminal applications
- Preserving status changes as an audit history
- Scheduling and clearing timezone-aware follow-ups
- Finding active applications that require follow-up
- Storing applications in an in-memory repository
- Exposing use cases through an application service
- Running a deterministic demonstration scenario
- Verifying behavior with automated tests

No web framework or database has been added yet. The domain behavior is developed and tested independently before infrastructure is introduced.

## Architecture

```text
Demo / future API
        |
        v
ApplicationService
        |
        v
ApplicationRepository (Protocol)
        |
        v
InMemoryApplicationRepository
        |
        v
Application domain model
```

The domain model owns business rules. The service coordinates application use cases. The repository abstraction separates storage decisions from business behavior.

## Project structure

```text
src/application_tracker/
├── __init__.py
├── demo.py
├── repositories.py
├── services.py
└── domain/
    ├── __init__.py
    ├── models.py
    └── validation.py

tests/
├── test_application.py
├── test_application_repository.py
├── test_application_service.py
└── test_demo.py
```

## Requirements

- Python 3.12 or later
- uv

## Setup

Install the project and its development dependencies:

```bash
uv sync
```

## Run the tests

```bash
uv run pytest -q
```

## Run the demo

```bash
uv run python -m application_tracker.demo
```

Expected output:

```text
All applications: 3
Needs follow-up as of 2026-08-20T00:00:00+00:00:
- OpenAI | Backend Engineer | screening
```

The demo uses fixed dates so that it produces deterministic output.

## Key engineering decisions

### Pure-Python domain first

The project starts without FastAPI or PostgreSQL so that business rules can be designed and tested independently from delivery and persistence technologies.

### Explicit domain behavior

Status changes and follow-up operations are performed through domain methods instead of allowing unrestricted attribute mutation. This keeps validation close to the state it protects.

### Status history

Status transitions are stored as immutable history records. The current status can be queried directly while previous transitions remain available as an audit trail.

### Timezone-aware datetimes

Follow-up calculations reject timezone-naive datetime values. This prevents ambiguous comparisons when the application later interacts with users or services in different time zones.

### Repository abstraction

`ApplicationService` depends on an `ApplicationRepository` protocol rather than a concrete database implementation. The current in-memory repository supports development and tests without committing the application layer to a persistence technology.

### Deterministic tests

Time-dependent behavior receives an explicit reference time. Tests do not depend on the computer's current clock, making failures repeatable and easier to debug.

## Next milestone

The next milestone will introduce persistent storage while preserving the existing domain and service behavior.
