# Deployment Contract

Application Lifecycle Tracker is packaged as two OCI-compatible containers: a FastAPI service and a React static frontend served by unprivileged NGINX.

## Runtime requirements

- Run both images as their built-in non-root users.
- Keep API port `8000` reachable from the frontend container.
- Expose frontend container port `8080` to users.
- Route API health checks to `GET /health` and frontend health checks to `GET /healthz`.
- Mount persistent writable storage at `/data`.
- Set `APPLICATION_TRACKER_DATABASE_PATH=/data/application_tracker.db`.
- Set `APPLICATION_TRACKER_LOG_LEVEL` to one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

The image starts the API with:

```text
uvicorn application_tracker.main:app --host 0.0.0.0 --port 8000
```

The frontend container serves compiled assets on port `8080` and proxies `/api/*` to the API container. The Compose development contract exposes the UI on `127.0.0.1:8080` and direct API debugging on `127.0.0.1:8001`.

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
cd frontend
npm ci
npm run lint
npm run test
npm run build
cd ..
docker compose config --quiet
docker compose build
```

## Post-deployment smoke test

```bash
curl --fail https://your-service.example/healthz
curl --fail https://your-service.example/api/health
```

Expected response:

```json
{"status": "ok"}
```

After the health check, create an application and retrieve it again after an instance restart to confirm that the platform volume is mounted correctly.

## Scaling path

Before running multiple API replicas, replace SQLite with a shared database such as PostgreSQL and provide a repository implementation that satisfies the existing `ApplicationRepository` protocol. Authentication and per-user ownership are also required before exposing personal application data as a multi-user public service.
