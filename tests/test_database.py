
"""Tests for database configuration and session management."""

from unittest.mock import MagicMock

from app.database import get_db


def test_get_db_yields_session_and_closes_it(monkeypatch):
    mock_session = MagicMock()

    monkeypatch.setattr(
        "app.database.SessionLocal",
        lambda: mock_session,
    )

    db_generator = get_db()

    # The generator should yield the created session.
    session = next(db_generator)
    assert session is mock_session

    # Closing the generator should execute the finally block.
    try:
        next(db_generator)
    except StopIteration:
        pass

    mock_session.close.assert_called_once()


def test_get_db_closes_session_after_exception(monkeypatch):
    mock_session = MagicMock()

    monkeypatch.setattr(
        "app.database.SessionLocal",
        lambda: mock_session,
    )

    db_generator = get_db()
    assert next(db_generator) is mock_session

    # Simulate a request ending with an exception.
    try:
        db_generator.throw(RuntimeError("Simulated request error"))
    except RuntimeError:
        pass

    mock_session.close.assert_called_once()
