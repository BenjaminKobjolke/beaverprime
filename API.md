# BeaverPrime API Documentation

This document describes the available API endpoints for the BeaverPrime application.

## Authentication

The API uses **Bearer Token authentication** (JWT).

### Authentication Flow

1. **Register** a new account using `/api/v1/auth/register` (optional - if you don't have an account)
2. **Login** using `/api/v1/auth/login` to receive an access token
3. **Use the token** in the `Authorization` header for all subsequent requests:
   ```
   Authorization: Bearer <your_access_token>
   ```

### Email Verification

If email verification is enabled in settings (`REQUIRE_VERIFICATION=true`):
- After registration, a verification email will be sent
- You must verify your email before you can login
- Check your email and click the verification link

## Available Endpoints

### Authentication Endpoints

#### Register

- **Endpoint**: `/api/v1/auth/register`
- **Method**: POST
- **Description**: Register a new user account
- **Authentication**: None required
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "your_secure_password"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "message": "User registered successfully. Please check your email to verify your account before logging in.",
    "user": {
      "id": "uuid-here",
      "email": "user@example.com",
      "is_active": true,
      "is_superuser": false,
      "is_verified": false
    },
    "verification_required": true
  }
  ```
- **Error Responses**:
  - 400 Bad Request: User already exists or invalid data
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
      "email": "user@example.com",
      "password": "your_secure_password"
    }'
  ```

#### Login

- **Endpoint**: `/api/v1/auth/login`
- **Method**: POST
- **Description**: Authenticate and receive an access token
- **Authentication**: None required
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "your_password"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-here",
      "email": "user@example.com",
      "is_active": true,
      "is_superuser": false,
      "is_verified": true
    }
  }
  ```
- **Error Responses**:
  - 401 Unauthorized: Incorrect email or password
  - 403 Forbidden: Email not verified (when verification is required)
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
      "email": "user@example.com",
      "password": "your_password"
    }'
  ```
- **Usage**: Save the `access_token` from the response and include it in all subsequent API requests

### Lists API

- **Endpoint**: `/api/v1/lists`
- **Method**: GET
- **Description**: Get all lists for the authenticated user
- **Authentication**: Requires Bearer token in Authorization header
- **Example Usage**:
  ```bash
  curl -X GET http://localhost:8000/api/v1/lists \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  ```
- **Response Format**:
  ```json
  [
    {
      "id": 1,
      "name": "List Name",
      "order": 0,
      "user_id": "uuid-here",
      "habits": []
    }
  ]
  ```

### Single Habit Completion API

- **Endpoint**: `/api/v1/habits/{habit_id}/completions`
- **Method**: POST
- **Description**: Toggle completion status for a single habit on a specific date
- **Authentication**: Requires Bearer token in Authorization header
- **URL Parameters**:
  - `habit_id`: The ID of the habit
- **Query Parameters**:
  - `date`: Date in YYYY-MM-DD format (e.g., "2025-02-13")
- **Example Usage**:

  ```bash
  # Toggle habit completion for a specific date
  curl -X POST "http://localhost:8000/api/v1/habits/123/completions?date=2025-02-13" \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  ```

- **Response Format**:
  ```json
  {
    "habit_id": 123,
    "color": "green",
    "state": "checked",
    "sorting": {
      "starred": false,
      "priority": 0,
      "order": 1,
      "name": "Exercise"
    }
  }
  ```
- **Notes**:
  - This endpoint toggles the completion status (cycles through: unset → checked → skipped → unset)
  - The `state` field can be:
    - `"checked"`: Habit is completed
    - `"skipped"`: Habit is skipped
    - `"unset"`: Habit is not marked
  - Returns 401 for invalid or missing token
  - Returns 404 if habit not found
  - Returns 400 for invalid date format

### Batch Update Habits API

- **Endpoint**: `/api/v1/habits/batch-completions`
- **Method**: POST
- **Description**: Toggle completion status for multiple dates for a habit at once
- **Authentication**: Requires Bearer token in Authorization header
- **Request Body**:
  - `habit_id`: The ID of the habit (integer)
  - `dates`: Array of date strings in YYYY-MM-DD format
- **Example Usage**:

  ```bash
  # Toggle multiple dates for a habit
  curl -X POST http://localhost:8000/api/v1/habits/batch-completions \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "habit_id": 123,
      "dates": [
        "2025-02-13",
        "2025-02-12",
        "2025-02-11"
      ]
    }'
  ```

- **Response Format**:
  ```json
  {
    "habit_id": 123,
    "updated": [
      {
        "date": "2025-02-13",
        "done": true
      },
      {
        "date": "2025-02-12",
        "done": false
      },
      {
        "date": "2025-02-11",
        "done": true
      }
    ]
  }
  ```
- **Notes**:
  - Dates should be in ISO format (YYYY-MM-DD)
  - Each date toggles the completion status independently
  - Invalid dates are skipped and logged
  - The `done` field in response indicates the new state:
    - `true`: Habit is completed
    - `false`: Habit is not completed
    - `null`: Habit is skipped
  - Returns 401 for invalid or missing token
  - Returns 404 if habit not found
  - Returns 500 for unexpected errors

### Export Habits API

- **Endpoint**: `/api/v1/export`
- **Method**: GET
- **Description**: Export all user habits and completion data in JSON format suitable for backup/restore
- **Authentication**: Requires Bearer token in Authorization header
- **Example Usage**:

  ```bash
  # Export all user data
  curl -X GET http://localhost:8000/api/v1/export \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  ```

- **Response Format**:
  ```json
  {
    "version": "2.0",
    "exported_at": "2025-02-13T10:30:00",
    "habits": [
      {
        "id": 1,
        "name": "Exercise",
        "list_id": 1,
        "order": 0,
        "completions": [
          {
            "date": "2025-02-13",
            "done": true
          },
          {
            "date": "2025-02-12",
            "done": false
          }
        ]
      }
    ]
  }
  ```
- **Notes**:
  - Returns all habits for the authenticated user
  - Includes all completion records for each habit
  - Response includes version info for compatibility
  - Can be used to backup and restore data
  - Returns 401 for invalid or missing token

---

## Testing the API

### Prerequisites

Before testing, ensure:
- The application is running (use `./start.bat dev` on Windows or `./start.sh dev` on Unix)
- You have access to the server (default: `http://localhost:8000`)
- Email verification is disabled for testing, or you have access to email verification links

### Automated Testing with Pytest

The project includes a comprehensive test suite for all API endpoints.

#### Running Tests

```bash
# Run all API tests
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::test_register_user -v

# Run tests with detailed output
pytest tests/test_api.py -v -s

# Run tests in parallel (faster)
pytest tests/test_api.py -v -n auto
```

#### Test Coverage

The test suite covers:
- ✅ User registration and authentication
- ✅ Login with valid/invalid credentials
- ✅ Bearer token authentication
- ✅ Lists CRUD operations
- ✅ Habits CRUD operations
- ✅ Habit completion toggling
- ✅ Batch completion updates
- ✅ Data export
- ✅ Authorization and error handling

### Manual Testing with curl

#### Complete Workflow Example

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Response: User created, check verification_required field

# 2. Login to get Bearer token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Response includes: {"access_token": "eyJ...", "token_type": "bearer", ...}
# Copy the access_token for use in subsequent requests

# 3. Get all lists (using token)
curl -X GET http://localhost:8000/api/v1/lists \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# 4. Create a new list
curl -X POST http://localhost:8000/api/v1/lists \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Health Goals",
    "order": 0
  }'

# Response includes: {"id": 1, "name": "Health Goals", ...}
# Note the list ID for creating habits

# 5. Create a habit in the list
curl -X POST http://localhost:8000/api/v1/lists/1/habits \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Exercise",
    "order": 0,
    "list_id": 1
  }'

# Response includes: {"id": 1, "name": "Morning Exercise", ...}

# 6. Toggle habit completion for today
curl -X POST "http://localhost:8000/api/v1/habits/1/completions?date=2025-02-13" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# 7. Export all data
curl -X GET http://localhost:8000/api/v1/export \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### Testing with Postman or Insomnia

#### Setup in Postman:

1. **Create a new Collection** named "BeaverHabits API"

2. **Set Base URL**: Create an environment variable
   - Variable: `base_url`
   - Value: `http://localhost:8000`

3. **Register User** (POST `{{base_url}}/api/v1/auth/register`)
   - Body (JSON):
     ```json
     {
       "email": "test@example.com",
       "password": "SecurePassword123!"
     }
     ```

4. **Login** (POST `{{base_url}}/api/v1/auth/login`)
   - Body (JSON):
     ```json
     {
       "email": "test@example.com",
       "password": "SecurePassword123!"
     }
     ```
   - In Tests tab, add script to save token:
     ```javascript
     pm.environment.set("bearer_token", pm.response.json().access_token);
     ```

5. **Configure Authorization** for subsequent requests:
   - Type: Bearer Token
   - Token: `{{bearer_token}}`

6. **Create requests** for other endpoints (lists, habits, export)

### Testing with Python httpx

```python
import httpx
import asyncio

async def test_api():
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Register
        register_response = await client.post(
            f"{base_url}/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePass123!"}
        )
        print(f"Register: {register_response.status_code}")

        # Login
        login_response = await client.post(
            f"{base_url}/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecurePass123!"}
        )
        token = login_response.json()["access_token"]
        print(f"Token: {token[:20]}...")

        # Get lists
        headers = {"Authorization": f"Bearer {token}"}
        lists_response = await client.get(
            f"{base_url}/api/v1/lists",
            headers=headers
        )
        print(f"Lists: {lists_response.json()}")

asyncio.run(test_api())
```

### Common Testing Scenarios

#### Test Invalid Authentication

```bash
# Missing token
curl -X GET http://localhost:8000/api/v1/lists
# Expected: 401 Unauthorized

# Invalid token
curl -X GET http://localhost:8000/api/v1/lists \
  -H "Authorization: Bearer invalid_token"
# Expected: 401 Unauthorized
```

#### Test Validation Errors

```bash
# Register with invalid email
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email", "password": "test"}'
# Expected: 422 Validation Error

# Toggle completion with invalid date
curl -X POST "http://localhost:8000/api/v1/habits/1/completions?date=invalid-date" \
  -H "Authorization: Bearer YOUR_TOKEN"
# Expected: 400 Bad Request
```

### Troubleshooting

#### Issue: "Email verification required"

**Solution**:
- Check `settings.ini` and set `require_verification = false` in the `[app]` section
- Or manually verify the user in the database

#### Issue: "401 Unauthorized" after login

**Possible causes**:
- Token expired (JWT_LIFETIME_SECONDS in configs)
- Token copied incorrectly (check for extra spaces)
- Wrong Authorization header format (must be `Bearer TOKEN`)

#### Issue: Tests fail with "could not translate host name"

**Solution**: Database connection issue - ensure database is running and settings.ini is configured

#### Issue: "404 Not Found" for API endpoints

**Solution**: Ensure you're using `/api/v1/` prefix for all API routes

### API Documentation

Access interactive API docs while the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Complete endpoint documentation
- Request/response schemas
- "Try it out" functionality for testing directly in browser
