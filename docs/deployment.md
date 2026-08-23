# Deployment Contract

Application Lifecycle Tracker is packaged as an OCI-compatible container. A deployment platform only needs to satisfy the runtime contract below.

## Runtime requirements

- Run the image as its built-in non-root user (`uid=10001`).
- Expose container port `8000`.
- Route health checks to `GET /health`.
- Mount persistent writable storage at `/data`.
- Set `APPLICATION_TRACKER_DATABASE_PATH=/data/application_tracker.db`.
- Set `APPLICATION_TRACKER_LOG_LEVEL` to one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

The image starts the API with:

```text
uvicorn application_tracker.main:app --host 0.0.0.0 --port 8000
```

## SQLite deployment constraint

The current V1 deployment must run as a single application replica. SQLite stores state in one database file and is not a shared database for horizontally scaled containers.

The `/data` mount must be backed by persistent storage. Deploying the container with an ephemeral filesystem will lose application data when the instance is replaced.

## Pre-deployment checks

Run the same checks enforced by CI:

```bash
uv sync --locked --dev
uv run ruff check .
uv run mypy
uv run pytest \
  --cov=application_tracker \
  --cov-report=term-missing \
  -q
docker compose config --quiet
docker build --tag application-lifecycle-tracker:release .
```

## Post-deployment smoke test

```bash
curl --fail https://your-service.example/health
```

Expected response:

```json
{"status": "ok"}
```

After the health check, create an application and retrieve it again after an instance restart to confirm that the platform volume is mounted correctly.

## Scaling path

Before running multiple API replicas, replace SQLite with a shared database such as PostgreSQL and provide a repository implementation that satisfies the existing `ApplicationRepository` protocol. Authentication and per-user ownership are also required before exposing personal application data as a multi-user public service.
