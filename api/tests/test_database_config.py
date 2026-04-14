"""Tests for database engine configuration."""

from sqlalchemy.pool import StaticPool

from app.core.database import build_engine_kwargs


def test_build_engine_kwargs_uses_queue_pool_defaults_for_postgres():
    kwargs = build_engine_kwargs('postgresql://user:pass@localhost:5432/filltheword')

    assert kwargs == {'pool_pre_ping': True}


def test_build_engine_kwargs_uses_static_pool_for_in_memory_sqlite():
    kwargs = build_engine_kwargs('sqlite:///:memory:')

    assert kwargs['pool_pre_ping'] is True
    assert kwargs['connect_args'] == {'check_same_thread': False}
    assert kwargs['poolclass'] is StaticPool


def test_build_engine_kwargs_uses_sqlite_thread_flags_for_file_sqlite():
    kwargs = build_engine_kwargs('sqlite:///./filltheword.db')

    assert kwargs['pool_pre_ping'] is True
    assert kwargs['connect_args'] == {'check_same_thread': False}
    assert 'poolclass' not in kwargs
