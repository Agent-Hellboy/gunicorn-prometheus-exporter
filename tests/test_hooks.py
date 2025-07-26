import logging
import os

from unittest.mock import MagicMock

import pytest

from gunicorn_prometheus_exporter import hooks


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    # ensure redis env var is cleared for tests
    monkeypatch.delenv("REDIS_ENABLED", raising=False)


def test_setup_prometheus_server_success(monkeypatch):
    logger = logging.getLogger("test")
    mock_registry = MagicMock()
    monkeypatch.setattr("gunicorn_prometheus_exporter.metrics.registry", mock_registry)
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.utils.get_multiprocess_dir", lambda: "/tmp"
    )
    mpc = MagicMock()
    monkeypatch.setattr("gunicorn_prometheus_exporter.hooks.MultiProcessCollector", mpc)

    port, registry = hooks._setup_prometheus_server(logger)

    assert port == hooks.config.prometheus_metrics_port
    assert registry is mock_registry
    mpc.assert_called_once_with(mock_registry)


def test_setup_prometheus_server_no_dir(monkeypatch):
    logger = logging.getLogger("test")
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.utils.get_multiprocess_dir", lambda: None
    )
    result = hooks._setup_prometheus_server(logger)
    assert result is None


def test_setup_prometheus_server_mpc_failure(monkeypatch):
    logger = logging.getLogger("test")
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.utils.get_multiprocess_dir", lambda: "/tmp"
    )
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks.MultiProcessCollector",
        MagicMock(side_effect=Exception("boom")),
    )
    result = hooks._setup_prometheus_server(logger)
    assert result is None


def test_default_on_starting(monkeypatch):
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.utils.get_multiprocess_dir", lambda: "/tmp"
    )
    ensure = MagicMock()
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.utils.ensure_multiprocess_dir", ensure
    )
    hooks.default_on_starting(None)
    ensure.assert_called_once_with("/tmp")


def test_default_on_starting_no_dir(monkeypatch):
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.utils.get_multiprocess_dir", lambda: None
    )
    ensure = MagicMock()
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.utils.ensure_multiprocess_dir", ensure
    )
    hooks.default_on_starting(None)
    ensure.assert_not_called()


def test_default_when_ready_success(monkeypatch):
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks._setup_prometheus_server",
        lambda logger: (1234, "reg"),
    )
    start = MagicMock()
    monkeypatch.setattr("gunicorn_prometheus_exporter.hooks.start_http_server", start)

    hooks.default_when_ready(None)
    start.assert_called_once_with(1234, registry="reg")


def test_default_when_ready_retry(monkeypatch):
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks._setup_prometheus_server",
        lambda logger: (1234, "reg"),
    )
    attempt = {"count": 0}

    def failing_start(port, registry):
        if attempt["count"] < 2:
            attempt["count"] += 1
            raise OSError(98, "in use")
        start_called.append((port, registry))

    start_called = []
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks.start_http_server", failing_start
    )
    monkeypatch.setattr("time.sleep", lambda s: None)

    hooks.default_when_ready(None)
    assert start_called == [(1234, "reg")]


def test_default_when_ready_setup_none(monkeypatch):
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks._setup_prometheus_server",
        lambda logger: None,
    )
    start = MagicMock()
    monkeypatch.setattr("gunicorn_prometheus_exporter.hooks.start_http_server", start)
    hooks.default_when_ready(None)
    start.assert_not_called()


def test_redis_when_ready_enabled(monkeypatch):
    os.environ["REDIS_ENABLED"] = "true"
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks._setup_prometheus_server",
        lambda logger: (1234, "reg"),
    )
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks.start_http_server", lambda *a, **k: None
    )
    start_forwarder = MagicMock()
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks.start_redis_forwarder", start_forwarder
    )

    hooks.redis_when_ready(None)
    start_forwarder.assert_called_once()


def test_redis_when_ready_disabled(monkeypatch):
    os.environ["REDIS_ENABLED"] = "false"
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks._setup_prometheus_server",
        lambda logger: (1234, "reg"),
    )
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks.start_http_server", lambda *a, **k: None
    )
    start_forwarder = MagicMock()
    monkeypatch.setattr(
        "gunicorn_prometheus_exporter.hooks.start_redis_forwarder", start_forwarder
    )

    hooks.redis_when_ready(None)
    start_forwarder.assert_not_called()
