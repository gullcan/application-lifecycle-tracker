from pathlib import Path

import pytest

from application_tracker.config import Settings


def test_settings_use_safe_defaults(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "APPLICATION_TRACKER_DATABASE_PATH",
        raising=False,
    )
    monkeypatch.delenv(
        "APPLICATION_TRACKER_LOG_LEVEL",
        raising=False,
    )

    settings = Settings.from_environment()

    assert settings.database_path == Path(
        "application_tracker.db"
    )
    assert settings.log_level == "INFO"


def test_settings_read_environment_values(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "APPLICATION_TRACKER_DATABASE_PATH",
        "/tmp/applications.db",
    )
    monkeypatch.setenv(
        "APPLICATION_TRACKER_LOG_LEVEL",
        "debug",
    )

    settings = Settings.from_environment()

    assert settings.database_path == Path(
        "/tmp/applications.db"
    )
    assert settings.log_level == "DEBUG"


def test_settings_reject_blank_database_path(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "APPLICATION_TRACKER_DATABASE_PATH",
        "   ",
    )

    with pytest.raises(
        ValueError,
        match="database path cannot be blank",
    ):
        Settings.from_environment()


def test_settings_reject_unknown_log_level(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "APPLICATION_TRACKER_LOG_LEVEL",
        "verbose",
    )

    with pytest.raises(
        ValueError,
        match="unsupported log level",
    ):
        Settings.from_environment()
