# Changelog

All notable changes to Application Lifecycle Tracker are documented in this file.

## [1.1.0] - 2026-08-24

### Added

- Editable company, role, source, job URL, and notes
- Recoverable application archiving
- Full-text search and configurable sorting
- CSV export for portable personal data
- Consistent SQLite backup and restore commands
- Isolated full-stack Playwright workflow in CI

## [1.0.0] - 2026-08-24

### Added

- Domain-driven job application lifecycle with explicit transition rules
- Immutable status history and timezone-aware follow-up scheduling
- FastAPI REST API with request validation and structured error responses
- SQLite persistence with transactional, versioned schema migrations
- React and TypeScript dashboard for creating and managing applications
- Status filtering, pagination, follow-up controls, and lifecycle history
- Structured JSON logging and environment-based runtime configuration
- Non-root API and frontend containers orchestrated with Docker Compose
- Backend and frontend automated tests and GitHub Actions quality checks

### Deployment scope

Version 1.0 is designed as a local-first, single-user application. Public multi-user hosting, authentication, and horizontally scaled deployment are intentionally outside its scope.
