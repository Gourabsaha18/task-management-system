
"""Automated tests for the Task Management System API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
from app.database import Base, get_db
from app.main import app


# Separate in-memory database for automated tests.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


def override_get_db():
    """Provide a database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Give every test a fresh database."""
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)


def register_user(
    client,
    username="pytest_user",
    email="pytest@example.com",
):
    """Register a user for testing."""
    return client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "StrongPass123!",
        },
    )


def login_user(client, email="pytest@example.com"):
    """Log in and return an access token."""
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "StrongPass123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token):
    """Create authorization headers for a token."""
    return {"Authorization": f"Bearer {token}"}


def create_task(client, headers, title="Test task"):
    """Create a task and return its response."""
    return client.post(
        "/tasks/",
        headers=headers,
        json={
            "title": title,
            "description": "Created by automated tests",
            "status": "pending",
            "priority": "high",
            "due_date": None,
        },
    )


# ---------- Public endpoints ----------

def test_homepage(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Task Management System API is running!"
    )


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ---------- Authentication ----------

def test_register_user(client):
    response = register_user(client)

    assert response.status_code == 201
    assert response.json()["username"] == "pytest_user"
    assert response.json()["email"] == "pytest@example.com"
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()


def test_duplicate_registration(client):
    assert register_user(client).status_code == 201

    response = register_user(client)

    assert response.status_code == 409


def test_login_success(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        data={
            "username": "pytest@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        data={
            "username": "pytest@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 401


def test_registration_validation(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "ab",
            "email": "not-an-email",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_tasks_require_authentication(client):
    response = client.get("/tasks/")

    assert response.status_code == 401


def test_invalid_token_returns_401(client):
    response = client.get(
        "/tasks/",
        headers={
            "Authorization": "Bearer invalid.token.value"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired authentication token"
    )
    assert response.headers["www-authenticate"] == "Bearer"


def test_missing_bearer_token_returns_401(client):
    response = client.get(
        "/tasks/",
        headers={"Authorization": "Bearer "},
    )

    assert response.status_code == 401


def test_valid_token_for_nonexistent_user_returns_401(client):
    from app.auth import create_access_token

    # The token is valid, but user ID 999999 does not exist.
    token = create_access_token(999999)

    response = client.get(
        "/tasks/",
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired authentication token"
    )


# ---------- Task CRUD ----------

def test_create_and_list_tasks(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    created = create_task(client, headers)

    assert created.status_code == 201

    task = created.json()
    assert task["title"] == "Test task"
    assert task["status"] == "pending"
    assert task["priority"] == "high"
    assert task["owner_id"] > 0

    listed = client.get("/tasks/", headers=headers)

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == task["id"]


def test_get_single_task(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    created = create_task(client, headers)
    task_id = created.json()["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_update_task(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    created = create_task(client, headers)
    task_id = created.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={
            "title": "Updated task",
            "status": "completed",
            "priority": "medium",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated task"
    assert response.json()["status"] == "completed"
    assert response.json()["priority"] == "medium"


def test_update_nonexistent_task_returns_404(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    response = client.patch(
        "/tasks/999999",
        headers=headers,
        json={"title": "Updated title"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_delete_task(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    created = create_task(client, headers)
    task_id = created.json()["id"]

    deleted = client.delete(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert deleted.status_code == 204

    missing = client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert missing.status_code == 404


# ---------- Filtering and error handling ----------

def test_filter_tasks_by_status(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    create_task(client, headers, "Pending task")

    completed = create_task(
        client,
        headers,
        "Completed task",
    )
    task_id = completed.json()["id"]

    update_response = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert update_response.status_code == 200

    response = client.get(
        "/tasks/",
        headers=headers,
        params={"status": "completed"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "completed"


def test_filter_tasks_by_priority(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    create_task(client, headers, "High priority task")

    response = client.get(
        "/tasks/",
        headers=headers,
        params={"priority": "low"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_invalid_task_status_filter(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    response = client.get(
        "/tasks/",
        headers=headers,
        params={"status": "invalid_status"},
    )

    assert response.status_code == 422


def test_task_not_found(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    response = client.get(
        "/tasks/999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_user_cannot_access_another_users_task(client):
    register_user(
        client,
        username="first_user",
        email="first@example.com",
    )
    first_headers = auth_headers(
        login_user(client, "first@example.com")
    )

    created = create_task(
        client,
        first_headers,
        "Private task",
    )
    task_id = created.json()["id"]

    register_user(
        client,
        username="second_user",
        email="second@example.com",
    )
    second_headers = auth_headers(
        login_user(client, "second@example.com")
    )

    response = client.get(
        f"/tasks/{task_id}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_task(client):
    register_user(
        client,
        username="first_user",
        email="first@example.com",
    )
    first_headers = auth_headers(
        login_user(client, "first@example.com")
    )

    created = create_task(
        client,
        first_headers,
        "Private task",
    )
    task_id = created.json()["id"]

    register_user(
        client,
        username="second_user",
        email="second@example.com",
    )
    second_headers = auth_headers(
        login_user(client, "second@example.com")
    )

    response = client.patch(
        f"/tasks/{task_id}",
        headers=second_headers,
        json={"title": "Unauthorized update"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

    original = client.get(
        f"/tasks/{task_id}",
        headers=first_headers,
    )

    assert original.status_code == 200
    assert original.json()["title"] == "Private task"

def test_token_missing_subject_returns_401(client, monkeypatch):
    from app.dependencies import decode_access_token

    monkeypatch.setattr(
        "app.dependencies.decode_access_token",
        lambda token: {},
    )

    response = client.get(
        "/tasks/",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired authentication token"
    )


def test_token_with_non_integer_subject_returns_401(
    client, monkeypatch
):
    monkeypatch.setattr(
        "app.dependencies.decode_access_token",
        lambda token: {"sub": "not-an-integer"},
    )

    response = client.get(
        "/tasks/",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 401


def test_token_with_null_subject_returns_401(
    client, monkeypatch
):
    monkeypatch.setattr(
        "app.dependencies.decode_access_token",
        lambda token: {"sub": None},
    )

    response = client.get(
        "/tasks/",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 401



def test_delete_nonexistent_task_returns_404(client):
    """Deleting a nonexistent task as an authenticated user returns 404."""
    register_response = register_user(client)
    assert register_response.status_code == 201

    token = login_user(client)
    headers = auth_headers(token)

    response = client.delete("/tasks/999999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_register_user_integrity_error_returns_409(client):
    """Registration rolls back and returns 409 on database integrity errors."""
    from app.database import get_db

    register_user(client, username="integrity_user", email="integrity@example.com")

    # Use a new username and email so the existing-user check passes.
    with patch("app.routers.users.hash_password", return_value="hashed-password"):
        with patch("app.routers.users.Session"):
            pass

    # Trigger the database commit error using a mocked session.
    class MockDB:
        def scalar(self, query):
            return None

        def add(self, user):
            pass

        def commit(self):
            raise IntegrityError("INSERT", {}, Exception("unique constraint"))

        def rollback(self):
            self.rolled_back = True

        def refresh(self, user):
            pass

    mock_db = MockDB()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.post(
            "/auth/register",
            json={
                "username": "integrity_user_2",
                "email": "integrity2@example.com",
                "password": "StrongPass123!",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email is already registered"
    assert mock_db.rolled_back is True
