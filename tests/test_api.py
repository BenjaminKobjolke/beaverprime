"""
Comprehensive API tests for BeaverHabits API endpoints.

Tests authentication, lists, habits, and export functionality with Bearer token authentication.
Run with: pytest tests/test_api.py -v
"""

import uuid
from datetime import date
import pytest
from httpx import AsyncClient, ASGITransport

from beaverhabits.main import app
from beaverhabits.app.db import create_db_and_tables
from beaverhabits.configs import settings


# Test configuration
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "SecureTestPassword123!"


@pytest.fixture(scope="session")
async def setup_database():
    """Set up test database before running tests."""
    await create_db_and_tables()
    yield


@pytest.fixture
async def client(setup_database):
    """Create async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def registered_user(client: AsyncClient):
    """Register a test user and return email and password."""
    email = TEST_EMAIL
    password = TEST_PASSWORD

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password}
    )

    assert response.status_code == 201, f"Registration failed: {response.text}"
    data = response.json()

    return {"email": email, "password": password, "user_data": data}


@pytest.fixture
async def auth_token(client: AsyncClient, registered_user):
    """Login and return Bearer token for authenticated requests."""
    # If email verification is required, we need to manually verify the user
    # For testing purposes, we'll try to login and handle verification if needed

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
    )

    # If verification is required and user is not verified, skip this test
    if response.status_code == 403:
        pytest.skip("Email verification required - skipping test requiring authentication")

    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()

    return data["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with Bearer token for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration endpoint."""
    unique_email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": TEST_PASSWORD}
    )

    assert response.status_code == 201
    data = response.json()

    assert "message" in data
    assert "user" in data
    assert data["user"]["email"] == unique_email
    assert "verification_required" in data
    assert data["verification_required"] == settings.REQUIRE_VERIFICATION


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient, registered_user):
    """Test registering with an already registered email fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": registered_user["email"],
            "password": "AnotherPassword123!"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user):
    """Test successful login returns access token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
    )

    # Skip if verification is required and user is not verified
    if response.status_code == 403:
        pytest.skip("Email verification required")

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == registered_user["email"]


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, registered_user):
    """Test login with wrong password fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
    )

    assert response.status_code == 401


# ============================================================================
# LISTS API TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_lists(client: AsyncClient, auth_headers):
    """Test getting all lists for authenticated user."""
    response = await client.get("/api/v1/lists", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_lists_unauthorized(client: AsyncClient):
    """Test getting lists without authentication fails."""
    response = await client.get("/api/v1/lists")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_list(client: AsyncClient, auth_headers):
    """Test creating a new list."""
    response = await client.post(
        "/api/v1/lists",
        headers=auth_headers,
        json={"name": "Test List", "order": 0}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Test List"
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_update_list(client: AsyncClient, auth_headers):
    """Test updating a list."""
    # First create a list
    create_response = await client.post(
        "/api/v1/lists",
        headers=auth_headers,
        json={"name": "Original Name", "order": 0}
    )
    assert create_response.status_code == 200
    list_id = create_response.json()["id"]

    # Then update it
    update_response = await client.patch(
        f"/api/v1/lists/{list_id}",
        headers=auth_headers,
        json={"name": "Updated Name", "order": 1}
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Name"
    assert data["order"] == 1


# ============================================================================
# HABITS API TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_habits(client: AsyncClient, auth_headers):
    """Test getting all habits for authenticated user."""
    response = await client.get("/api/v1/habits", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_habit_in_list(client: AsyncClient, auth_headers):
    """Test creating a habit in a list."""
    # First create a list
    list_response = await client.post(
        "/api/v1/lists",
        headers=auth_headers,
        json={"name": "Habit List", "order": 0}
    )
    assert list_response.status_code == 200
    list_id = list_response.json()["id"]

    # Then create a habit in that list
    habit_response = await client.post(
        f"/api/v1/lists/{list_id}/habits",
        headers=auth_headers,
        json={"name": "Exercise", "order": 0, "list_id": list_id}
    )

    assert habit_response.status_code == 200
    data = habit_response.json()
    assert data["name"] == "Exercise"
    assert data["list_id"] == list_id
    assert "id" in data


@pytest.mark.asyncio
async def test_get_habit_details(client: AsyncClient, auth_headers):
    """Test getting details of a specific habit."""
    # First create a list and habit
    list_response = await client.post(
        "/api/v1/lists",
        headers=auth_headers,
        json={"name": "Test List", "order": 0}
    )
    list_id = list_response.json()["id"]

    habit_response = await client.post(
        f"/api/v1/lists/{list_id}/habits",
        headers=auth_headers,
        json={"name": "Test Habit", "order": 0, "list_id": list_id}
    )
    habit_id = habit_response.json()["id"]

    # Get habit details
    detail_response = await client.get(
        f"/api/v1/habits/{habit_id}",
        headers=auth_headers
    )

    assert detail_response.status_code == 200
    data = detail_response.json()
    assert data["id"] == habit_id
    assert data["name"] == "Test Habit"


@pytest.mark.asyncio
async def test_toggle_habit_completion(client: AsyncClient, auth_headers):
    """Test toggling habit completion for a specific date."""
    # Create list and habit
    list_response = await client.post(
        "/api/v1/lists",
        headers=auth_headers,
        json={"name": "Test List", "order": 0}
    )
    list_id = list_response.json()["id"]

    habit_response = await client.post(
        f"/api/v1/lists/{list_id}/habits",
        headers=auth_headers,
        json={"name": "Daily Habit", "order": 0, "list_id": list_id}
    )
    habit_id = habit_response.json()["id"]

    # Toggle completion
    test_date = date.today().isoformat()
    toggle_response = await client.post(
        f"/api/v1/habits/{habit_id}/completions?date={test_date}",
        headers=auth_headers
    )

    assert toggle_response.status_code == 200
    data = toggle_response.json()
    assert "habit_id" in data
    assert "state" in data
    assert data["state"] in ["checked", "skipped", "unset"]


@pytest.mark.asyncio
async def test_batch_toggle_completions(client: AsyncClient, auth_headers):
    """Test batch toggling habit completions for multiple dates."""
    # Create list and habit
    list_response = await client.post(
        "/api/v1/lists",
        headers=auth_headers,
        json={"name": "Test List", "order": 0}
    )
    list_id = list_response.json()["id"]

    habit_response = await client.post(
        f"/api/v1/lists/{list_id}/habits",
        headers=auth_headers,
        json={"name": "Weekly Habit", "order": 0, "list_id": list_id}
    )
    habit_id = habit_response.json()["id"]

    # Batch toggle
    dates = [
        date.today().isoformat(),
        date.today().replace(day=date.today().day-1).isoformat(),
    ]

    batch_response = await client.post(
        "/api/v1/habits/batch-completions",
        headers=auth_headers,
        json={"habit_id": habit_id, "dates": dates}
    )

    assert batch_response.status_code == 200
    data = batch_response.json()
    assert "habit_id" in data
    assert "updated" in data
    assert isinstance(data["updated"], list)


# ============================================================================
# EXPORT API TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_export_user_data(client: AsyncClient, auth_headers):
    """Test exporting all user data."""
    response = await client.get("/api/v1/export", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "version" in data
    assert "exported_at" in data
    assert "habits" in data
    assert isinstance(data["habits"], list)


@pytest.mark.asyncio
async def test_export_unauthorized(client: AsyncClient):
    """Test export without authentication fails."""
    response = await client.get("/api/v1/export")

    assert response.status_code == 401


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_invalid_bearer_token(client: AsyncClient):
    """Test request with invalid Bearer token fails."""
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}

    response = await client.get("/api/v1/lists", headers=invalid_headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_habit_not_found(client: AsyncClient, auth_headers):
    """Test accessing non-existent habit returns 404."""
    response = await client.get(
        "/api/v1/habits/999999",
        headers=auth_headers
    )

    assert response.status_code == 404
