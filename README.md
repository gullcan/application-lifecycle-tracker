# Application Lifecycle Tracker

A Python backend core for tracking job applications, lifecycle transitions, status history, and follow-up schedules.

## Problem

Job seekers often manage applications across multiple platforms, emails, referrals, and company portals. As the number of applications grows, it becomes difficult to answer questions such as:

- Which applications are still active?
- What stage is each application in?
- How did an application reach its current status?
- Which applications require follow-up today?
- Which applications are already closed?

Application Lifecycle Tracker models this workflow as explicit domain rules instead of treating applications as simple CRUD records.

## Current milestone

The second milestone adds SQLite persistence to the existing pure-Python domain and service layers.

Current capabilities include:

- Creating job applications with validated company and job-title values
- Representing lifecycle states with an enum
- Enforcing valid status transitions
- Preventing changes to terminal applications
- Preserving status changes as an immutable audit history
- Scheduling and clearing timezone-aware follow-ups
- Finding active applications that require follow-up
- Storing applications in memory or SQLite
- Restoring application identity, timestamps, follow-ups, and status history
- Persisting status and follow-up mutations
- Exposing use cases through an application service
- Running a deterministic demonstration scenario
- Verifying domain, repository, service, and persistence behavior with automated tests

SQLite persistence was added without changing the public domain and service APIs. No web framework has been introduced yet.

## Architecture

```text
Demo / future API
        |
        v
ApplicationService
     |          |
     v          v
Domain      ApplicationRepository (Protocol)
model               |
             ┌──────┴──────┐
             v             v
        In-memory        SQLite
        repository      repository
                            |
                            v
                       SQLite database
```

The domain model owns business rules.

The service coordinates application use cases and persistence operations.

The repository protocol separates storage decisions from application behavior. Both in-memory and SQLite implementations satisfy the same repository contract.

## Project structure

```text
src/application_tracker/
├── __init__.py
├── demo.py
├── repositories.py
├── services.py
├── sqlite_repository.py
└── domain/
    ├── __init__.py
    ├── models.py
    └── validation.py

tests/
├── test_application.py
├── test_application_repository.py
├── test_application_service.py
├── test_demo.py
├── test_sqlite_repository.py
└── test_sqlite_service_integration.py
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

The demo uses fixed dates so that it produces deterministic output. It currently uses the in-memory repository, while SQLite persistence is verified through repository and service integration tests.

## Key engineering decisions

### Pure-Python domain first

The project began without a web framework or database so that business rules could be designed and tested independently from delivery and persistence technologies.

### Explicit domain behavior

Status changes and follow-up operations are performed through domain methods instead of unrestricted attribute mutation. This keeps validation close to the state it protects.

### Status history

Status transitions are stored as immutable history records. The current status can be queried directly while previous transitions remain available as an audit trail.

### Timezone-aware datetimes

Follow-up calculations reject timezone-naive datetime values. This prevents ambiguous comparisons when the application interacts with users or services in different time zones.

### Repository abstraction

`ApplicationService` depends on an `ApplicationRepository` protocol rather than a concrete storage implementation.

The project currently provides:

- `InMemoryApplicationRepository` for fast unit tests and demonstrations
- `SQLiteApplicationRepository` for persistent local storage

The service and domain layers do not need to change when the storage adapter changes.

### Explicit entity restoration

Creating a new application and restoring an existing application are separate lifecycle operations.

`Application.restore()` preserves persisted identity, creation time, current status, follow-up schedule, and status history without exposing private state to repository implementations.

### Transactional persistence

An application and its status history are written within the same SQLite transaction. If one operation fails, the transaction is rolled back instead of leaving partially stored state.

### Storage type conversion

Domain values are converted into SQLite-compatible values:

```text
UUID       → string
Enum       → string value
datetime   → ISO 8601 string
None       → SQL NULL
```

These values are converted back into domain types when an application is restored.

### Correctness before query optimization

Follow-up filtering continues to use the domain model so that terminal-status and timezone rules have a single source of truth.

The current SQLite query implementation favors correctness and clarity. Bulk hydration and query optimization can be introduced when real performance requirements appear.

### Deterministic tests

Time-dependent behavior receives an explicit reference time. Tests do not depend on the computer's current clock, making failures repeatable and easier to debug.

SQLite integration tests use temporary database files and open new repository instances to prove that state is persisted to disk rather than retained only in memory.

## Next milestone

The next milestone will expose the existing application use cases through a FastAPI REST API.

The API layer will:

- Validate HTTP request data
- Translate requests into application service calls
- Return structured JSON responses
- Map domain and repository exceptions to appropriate HTTP status codes
- Use SQLite persistence without moving business rules into route handlers
```

