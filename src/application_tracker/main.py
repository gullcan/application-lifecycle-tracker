import os

from application_tracker.bootstrap import build_app


database_path = os.getenv(
    "APPLICATION_TRACKER_DATABASE_PATH",
    "application_tracker.db",
)

app = build_app(database_path)
