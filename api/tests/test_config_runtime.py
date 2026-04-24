"""Tests for runtime configuration validation helpers."""

import importlib
import json
import logging
from types import SimpleNamespace

import pytest


def _reload_config_module(monkeypatch, **kwargs):
    env_keys = [
        "DATABASE_URL",
        "SECRET_KEY",
        "ENVIRONMENT",
        "STRICT_CONFIG",
        "DEBUG",
        "ALLOWED_HOSTS",
    ]
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)

    defaults = {
        "DATABASE_URL": "postgresql://user:pass@db:5432/wordbridge",
        "ALLOWED_HOSTS": json.dumps(["http://localhost:3007"]),
        "ENVIRONMENT": "development",
        "DEBUG": "false",
        "STRICT_CONFIG": "false",
        "SECRET_KEY": "test-secret-key",
    }
    defaults.update(kwargs)

    for key, value in defaults.items():
        monkeypatch.setenv(key, value)

    # ensure config is fully rebuilt with the test environment
    config_module = importlib.import_module("app.core.config")
    return importlib.reload(config_module)


def test_collect_runtime_issues_reports_placeholder_secret(monkeypatch):
    """placeholder secrets should be flagged as runtime issues."""
    config = _reload_config_module(monkeypatch, SECRET_KEY="change-me")
    issues = config.collect_runtime_issues()

    assert any("placeholder value" in issue for issue in issues)
    assert config.ensure_runtime_safety() == issues


def test_collect_runtime_issues_allows_strict_mode_when_clean(monkeypatch):
    """Strict mode should pass when issues are resolved."""
    config = _reload_config_module(
        monkeypatch,
        SECRET_KEY="super-long-and-random-key",
        STRICT_CONFIG="true",
    )

    assert config.collect_runtime_issues() == []
    assert config.ensure_runtime_safety() == []


def test_collect_runtime_issues_blocks_strict_mode(monkeypatch):
    """Strict mode should raise when known issues are present."""
    config = _reload_config_module(
        monkeypatch,
        SECRET_KEY="secret",
        STRICT_CONFIG="true",
    )

    with pytest.raises(RuntimeError, match="Strict runtime validation failed"):
        config.ensure_runtime_safety()


def test_run_startup_checks_uses_lifespan_helper_in_debug_mode(monkeypatch, caplog):
    """Startup checks should stay testable outside FastAPI event decorators."""
    main_module = importlib.import_module("app.main")

    monkeypatch.setattr(main_module, "settings", SimpleNamespace(DEBUG=True))
    monkeypatch.setattr(main_module, "collect_runtime_issues", lambda: ["placeholder issue"])

    def fail_if_called():
        raise AssertionError("debug startup should not enforce strict safety")

    monkeypatch.setattr(main_module, "ensure_runtime_safety", fail_if_called)

    with caplog.at_level(logging.WARNING):
        main_module.run_startup_checks()

    assert "placeholder issue" in caplog.text
