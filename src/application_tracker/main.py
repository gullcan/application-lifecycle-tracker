from application_tracker.bootstrap import build_app
from application_tracker.config import Settings
from application_tracker.logging_config import (
    configure_logging,
)


settings = Settings.from_environment()

configure_logging(settings.log_level)

app = build_app(settings.database_path)
