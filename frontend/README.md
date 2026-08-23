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

## Production image

```bash
docker build --tag application-lifecycle-tracker-frontend:local .
```

The multi-stage build compiles static assets with Node.js, then serves only the build output from an unprivileged NGINX image on port `8080`.
