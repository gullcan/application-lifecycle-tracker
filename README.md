# Application Lifecycle Tracker

[![CI](https://github.com/gullcan/application-lifecycle-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/gullcan/application-lifecycle-tracker/actions/workflows/ci.yml)

A production-aware Python backend API for tracking job applications, lifecycle transitions, status history, and follow-up schedules.

## Problem

Job seekers often manage applications across multiple platforms, emails, referrals, and company portals. As the number of applications grows, it becomes difficult to answer questions such as:

- Which applications are still active?
- What stage is each application in?
- How did an application reach its current status?
- Which applications require follow-up today?
- Which applications are already closed?

Application Lifecycle Tracker models this workflow as explicit domain rules instead of treating applications as simple CRUD records.

## Current capabilities

The project currently provides a persistent REST API with:

- Job application creation and retrieval
- Explicit lifecycle transition rules with immutable audit history
- Accepted, rejected, and withdrawn terminal outcomes
- Terminal-status and duplicate-transition protection
- Timezone-aware follow-up scheduling
- Follow-up queries for applications requiring attention
- Status filtering and limit/offset pagination
- SQLite persistence across process restarts
- Versioned and transactional SQLite schema migrations
- Structured request and response validation
- HTTP error mapping for validation, conflicts, and missing resources
- Interactive OpenAPI documentation
- A non-root Docker runtime
- Persistent container storage through a named volume
- Container health checks
- Environment-based runtime configuration and structured JSON logging
- Automated linting, strict type checking, coverage enforcement, Compose validation, and image builds in CI

## Architecture

```text
HTTP client
    |
    v
FastAPI routes and schemas
    |
    v
ApplicationService
    |
    +--------------------+
    |                    |
    v                    v
Application domain   ApplicationRepository (Protocol)
                         |
                  +------+------+
                  |             |
                  v             v
              In-memory       SQLite
              repository     repository
                                  |
                                  v
                           SQLite database
```

The domain model owns business rules and protects application state.

The service layer coordinates application use cases without depending on HTTP or SQLite details.

FastAPI translates HTTP requests into service calls and converts application results into response schemas.

The repository protocol keeps persistence replaceable. Runtime composition selects SQLite, while unit tests and demonstrations can use the in-memory implementation.

Detailed trade-offs are recorded in [Architecture Decisions](docs/architecture-decisions.md).

## Project structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── architecture-decisions.md
│   └── deployment.md
├── src/
│   └── application_tracker/
│       ├── __init__.py
│       ├── api.py
│       ├── bootstrap.py
│       ├── config.py
│       ├── demo.py
│       ├── logging_config.py
│       ├── main.py
│       ├── migrations.py
│       ├── repositories.py
│       ├── services.py
│       ├── sqlite_repository.py
│       └── domain/
│           ├── __init__.py
│           ├── models.py
│           └── validation.py
├── tests/
│   ├── test_api.py
│   ├── test_application.py
│   ├── test_application_repository.py
│   ├── test_application_service.py
│   ├── test_bootstrap.py
│   ├── test_config.py
│   ├── test_demo.py
│   ├── test_logging.py
│   ├── test_migrations.py
│   ├── test_sqlite_repository.py
│   └── test_sqlite_service_integration.py
├── .dockerignore
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── README.md
└── uv.lock
```

## Requirements

For local development:

- Python 3.12 or later
- uv

For containerized execution:

- Docker Desktop
- Docker Compose

## Setup

Install the project and its development dependencies:

```bash
uv sync
```

## Run the API locally

Start the development server:

```bash
uv run uvicorn application_tracker.main:app --reload
```

The application is then available at:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

By default, application data is stored in `application_tracker.db`.

The database location can be changed through an environment variable:

```bash
APPLICATION_TRACKER_DATABASE_PATH=/path/to/applications.db \
uv run uvicorn application_tracker.main:app
```

The application log level defaults to `INFO` and can be configured with:

```bash
APPLICATION_TRACKER_LOG_LEVEL=DEBUG \
uv run uvicorn application_tracker.main:app
```

Supported log levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.

## Lifecycle transitions

| Current status | Allowed next statuses |
|---|---|
| `draft` | `applied`, `withdrawn` |
| `applied` | `screening`, `interview`, `offer`, `rejected`, `withdrawn` |
| `screening` | `interview`, `offer`, `rejected`, `withdrawn` |
| `interview` | `offer`, `rejected`, `withdrawn` |
| `offer` | `accepted`, `rejected`, `withdrawn` |
| `accepted` | Terminal |
| `rejected` | Terminal |
| `withdrawn` | Terminal |

## Run with Docker Compose

Build and start the API:

```bash
docker compose up --build --detach
```

Check the container state:

```bash
docker compose ps
```

Verify the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Stop and remove the container:

```bash
docker compose down
```

SQLite data is stored in the named `application-data` volume and remains available when the container is removed and recreated.

For platform requirements, persistence constraints, and smoke tests, see the [Deployment Contract](docs/deployment.md).

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/applications` | Create an application |
| `GET` | `/applications` | List, filter, and paginate applications |
| `GET` | `/applications/follow-ups` | Find applications requiring follow-up |
| `GET` | `/applications/{application_id}` | Retrieve one application |
| `PATCH` | `/applications/{application_id}/status` | Change application status |
| `PUT` | `/applications/{application_id}/follow-up` | Schedule a follow-up |
| `DELETE` | `/applications/{application_id}/follow-up` | Clear a follow-up |
| `GET` | `/health` | Report API health |

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

The demo uses fixed dates so that it produces deterministic output. It uses the in-memory repository, while the production entry point uses SQLite persistence.

## Key engineering decisions

### Pure-Python domain first

The project began without a web framework or database so that business rules could be designed and tested independently from delivery and persistence technologies.

### Explicit domain behavior

Status changes and follow-up operations are performed through domain methods instead of unrestricted attribute mutation. This keeps validation close to the state it protects.

Lifecycle transitions are represented as an explicit policy. The model permits forward progress when hiring processes skip intermediate stages, rejects backward transitions, and closes accepted, rejected, or withdrawn applications as terminal outcomes.

### Status history

Status transitions are stored as immutable history records. The current status can be queried directly while previous transitions remain available as an audit trail.

### Timezone-aware datetimes

Follow-up calculations reject timezone-naive datetime values. This prevents ambiguous comparisons when the application interacts with users or services in different time zones.

### Repository abstraction

`ApplicationService` depends on an `ApplicationRepository` protocol rather than a concrete storage implementation.

The project provides:

- `InMemoryApplicationRepository` for fast unit tests and demonstrations
- `SQLiteApplicationRepository` for persistent local storage

The service and domain layers do not need to change when the storage adapter changes.

### Explicit entity restoration

Creating a new application and restoring an existing application are separate lifecycle operations.

`Application.restore()` preserves persisted identity, creation time, current status, follow-up schedule, and status history without exposing private state to repository implementations.

### Transactional persistence

An application and its status history are written within the same SQLite transaction. If one operation fails, the transaction is rolled back instead of leaving partially stored state.

### Versioned schema migrations

SQLite's `PRAGMA user_version` records the schema version inside the database file. Ordered migrations run transactionally during repository startup, preserve legacy data, and reject database versions newer than the application supports.

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

Follow-up filtering uses the domain model so that terminal-status and timezone rules have a single source of truth.

The current SQLite implementation favors correctness and clarity. Bulk hydration and further query optimization can be introduced when real performance requirements appear.

### Dependency composition

Repository construction is kept outside route handlers. The composition root selects SQLite and injects it into the API through the repository contract.

This keeps HTTP delivery, application coordination, domain behavior, and persistence responsibilities separate.

### Containerized runtime

Application code and runtime dependencies are installed into an immutable Docker image.

SQLite data is written to `/data` and persisted independently through a named Docker volume. The API process runs as a dedicated non-root user.

### Runtime configuration and observability

Database location and log level are loaded from validated environment variables. HTTP middleware records successful and failed requests as structured JSON with method, path, status code, duration, and exception context without logging request bodies.

### Deterministic tests

Time-dependent behavior receives an explicit reference time. Tests do not depend on the computer's current clock, making failures repeatable and easier to debug.

SQLite integration tests use temporary database files and new repository instances to prove that state is persisted to disk rather than retained only in memory.

## Quality checks

Run static analysis:

```bash
uv run ruff check .
```

Run strict type checking:

```bash
uv run mypy
```

Run the complete automated test suite with branch coverage:

```bash
uv run pytest \
  --cov=application_tracker \
  --cov-report=term-missing \
  -q
```

Coverage below 90% fails the quality check.

Validate the Compose configuration:

```bash
docker compose config --quiet
```

Build the container image:

```bash
docker build --tag application-lifecycle-tracker:local .
```

GitHub Actions runs static analysis, strict type checking, coverage-enforced tests, Compose validation, and the Docker image build for every push and pull request.

## Roadmap

Potential future improvements include:

- PostgreSQL support
- Authentication and user ownership
- Deployment configuration
- Metrics and operational monitoring
