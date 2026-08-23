# Application Lifecycle Tracker Frontend

React and TypeScript client for the Application Lifecycle Tracker API.

## Development

Run the FastAPI service on `127.0.0.1:8000`, then:

```bash
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api/*` requests to FastAPI.

## Quality checks

```bash
npm run lint
npm run test
npm run build
```

Tests use Vitest, jsdom, and Testing Library. They query controls by accessible labels and roles so the tests exercise the interface in the same way a user does.

The full-stack Playwright workflow expects an isolated Compose stack on port `18080`:

```bash
COMPOSE_PROJECT_NAME=application-tracker-e2e \
APPLICATION_TRACKER_API_PORT=18081 \
APPLICATION_TRACKER_FRONTEND_PORT=18080 \
docker compose -f ../compose.yaml up --build --detach --wait

PLAYWRIGHT_BASE_URL=http://127.0.0.1:18080 npm run test:e2e
```

## Production image

```bash
docker build --tag application-lifecycle-tracker-frontend:local .
```

The multi-stage build compiles static assets with Node.js, then serves only the build output from an unprivileged NGINX image on port `8080`.
