# Architecture Decisions

This document records the decisions that shape Application Lifecycle Tracker and the trade-offs behind them.

## 1. Keep business rules in a framework-independent domain model

**Decision:** Lifecycle transitions, follow-up rules, validation, and status history belong to the `Application` domain model.

**Problem solved:** The same rules must hold whether an application is changed through HTTP, a script, or a future delivery mechanism.

**Trade-off:** Route handlers cannot update fields directly; they must call explicit domain methods.

**Deferred alternative:** Framework-coupled ORM models were avoided because they would bind business behavior to persistence and HTTP concerns.

## 2. Coordinate use cases through an application service

**Decision:** FastAPI routes call `ApplicationService` rather than repositories or domain objects directly.

**Problem solved:** Use-case orchestration and persistence are kept out of HTTP handlers.

**Trade-off:** The service adds one level of indirection, but it provides a stable boundary for future delivery mechanisms.

## 3. Depend on a repository protocol

**Decision:** The service depends on `ApplicationRepository`, implemented by in-memory and SQLite adapters.

**Problem solved:** Unit tests can run without disk I/O, while runtime data persists without changing domain or service code.

**Trade-off:** Both implementations must honor the same behavior and error contracts.

**Deferred alternative:** SQLAlchemy was not introduced because the current storage model is small and the standard-library `sqlite3` module solves the active persistence requirements.

## 4. Preserve status transitions as an audit trail

**Decision:** The current status and immutable transition records are stored together.

**Problem solved:** The system can answer both “where is this application now?” and “how did it get there?”

**Trade-off:** Persistence updates must keep the entity and its history transactionally consistent.

## 5. Model lifecycle transitions explicitly

**Decision:** Allowed transitions are represented as a domain policy. Backward transitions are rejected, selected intermediate stages may be skipped, and accepted, rejected, and withdrawn outcomes are terminal.

**Problem solved:** An Enum restricts possible values but does not prevent semantically invalid movement between valid values.

**Trade-off:** Changing the hiring workflow requires an intentional policy update and accompanying tests.

## 6. Require timezone-aware datetimes

**Decision:** Follow-up and persisted timestamps reject timezone-naive values.

**Problem solved:** Comparisons remain unambiguous across machines, users, and future deployments in different time zones.

**Trade-off:** API clients must include a UTC offset in datetime values.

## 7. Version the SQLite schema

**Decision:** Ordered migrations use SQLite's `PRAGMA user_version` and run transactionally at repository startup.

**Problem solved:** Existing database files can evolve without losing user data, and newer unsupported schemas fail fast.

**Trade-off:** Migration functions are maintained manually while the project remains on `sqlite3`.

**Deferred alternative:** Alembic is deferred until adopting SQLAlchemy or reaching a schema size that justifies a dedicated migration framework.

## 8. Load and validate runtime configuration at startup

**Decision:** Database path and log level are read into an immutable settings object at the composition root.

**Problem solved:** Invalid runtime configuration is rejected before the API begins serving requests.

**Trade-off:** Adding a setting requires updating the settings model and its tests.

## 9. Log HTTP outcomes as structured JSON

**Decision:** Middleware records method, path, status, duration, and exception context without request bodies.

**Problem solved:** Operational events are machine-readable and consistent across endpoints.

**Trade-off:** Application and Uvicorn access logs may both appear unless deployment logging is configured to select one source.

**Security consideration:** Request bodies and query strings are excluded to reduce the risk of recording credentials or personal data.

## 10. Package the API as a non-root container

**Decision:** The application runs in an immutable image as a dedicated user, while SQLite data lives in a named volume.

**Problem solved:** Runtime code is reproducible and replaceable without coupling persistent data to a container lifecycle.

**Trade-off:** SQLite remains appropriate for a single-instance deployment; horizontal scaling would require a shared database such as PostgreSQL.

## 11. Enforce quality before merge

**Decision:** CI runs backend and frontend linting, strict Python type checking, backend coverage enforcement, frontend component tests, production builds, Compose validation, and container builds.

**Problem solved:** Pull requests cannot rely only on local success or manual review.

**Trade-off:** CI takes longer, but failures are detected before reaching `main`.

## 12. Keep the frontend as an explicit API client

**Decision:** React and TypeScript consume the existing HTTP contract instead of importing or duplicating Python application code.

**Problem solved:** Browser delivery remains independently testable while the domain and service layers stay framework-independent.

**Trade-off:** Request and response types exist in both Pydantic and TypeScript. Contract generation is deferred until schema drift becomes a demonstrated maintenance problem.

## 13. Keep lifecycle authority in the backend

**Decision:** The frontend presents lifecycle actions but does not duplicate the complete allowed-transition matrix.

**Problem solved:** Invalid transitions remain impossible for every client, not only the React interface.

**Trade-off:** A user can select a transition that the API rejects with `409 Conflict`. A future endpoint may expose allowed actions when richer UX justifies the additional contract.

## 14. Serve the frontend through a non-root gateway

**Decision:** A dedicated unprivileged NGINX container serves immutable frontend assets and proxies `/api/*` to FastAPI over the Compose network.

**Problem solved:** Development and production remain same-origin from the browser's perspective without opening a permissive CORS policy.

**Trade-off:** Deployment contains two processes and images, but each retains a focused responsibility and can be built independently.

## Deferred V2 scope

- Authentication and per-user ownership
- PostgreSQL and multi-instance deployment
- Metrics and distributed tracing

These features are intentionally outside the local-first, single-user product scope.

## 15. Prefer recoverable archiving over record deletion

**Decision:** Applications can be archived and restored. The product does not permanently delete application records.

**Problem solved:** Old or mistaken records can leave the active workspace without destroying lifecycle history or personal notes.

**Trade-off:** Queries must explicitly decide whether archived records are included.

## 16. Keep personal metadata in the application aggregate

**Decision:** Source, job URL, and notes are persisted with the application and updated through one domain operation.

**Problem solved:** The information needed for daily job-search work remains portable with the lifecycle record.

**Trade-off:** Notes are intentionally plain text; collaboration and rich-text editing are outside scope.

## 17. Run browser tests against an isolated stack

**Decision:** Playwright uses a separate Compose project, ports, and named volume.

**Problem solved:** Full-stack tests prove the React–NGINX–FastAPI–SQLite path without modifying a developer's personal database.

**Trade-off:** CI downloads a browser and builds containers, increasing execution time.
