# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.12.5 AS uv

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync \
    --locked \
    --no-dev \
    --no-editable

RUN useradd \
        --create-home \
        --uid 10001 \
        appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

ENV PATH="/app/.venv/bin:$PATH" \
    APPLICATION_TRACKER_DATABASE_PATH="/data/application_tracker.db"

USER appuser

EXPOSE 8000

CMD ["uvicorn", "application_tracker.main:app", "--host", "0.0.0.0", "--port", "8000"]
