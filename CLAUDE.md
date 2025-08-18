# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Beaver Prime Habit Tracker is a self-hosted habit tracking application built with FastAPI and NiceGUI. This fork adds enhanced features including list support, weekly goals, letter filtering, and a comprehensive API.

## Tech Stack

- **Backend**: FastAPI with async SQLAlchemy
- **Frontend**: NiceGUI (Python-based reactive UI framework)
- **Database**: PostgreSQL (production) or SQLite (development)
- **Authentication**: FastAPI-Users with JWT tokens
- **Package Management**: UV (recommended) or pip

## Development Commands

### Setup and Running
```bash
# Install dependencies with UV (recommended)
uv venv && uv sync

# Start development server (Windows)
./start.bat dev

# Start development server (Unix/Linux)
./start.sh dev

# Production mode (Windows)
./start.bat

# Production mode (Unix/Linux)
./start.sh prd
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run tests with async support
pytest -v --asyncio-mode=auto

# Available test files:
# - tests/test_auth.py - Authentication tests
# - tests/test_main_page.py - Main page UI tests
# - tests/test_storage.py - Storage tests
```

### Environment Variables
```bash
# Development mode
LOGURU_LEVEL=DEBUG           # Set to DEBUG in dev, WARNING in production
UVICORN_LOG_LEVEL=debug      # Set to debug in dev, warning in production

# Production mode
NICEGUI_STORAGE_PATH=.user\.nicegui  # Storage path for NiceGUI data

# Optional
SENTRY_DSN=<your-sentry-dsn>  # For error tracking
```

### Email Configuration

Email verification and password reset functionality requires SMTP configuration in `settings.ini`:

```ini
[email]
# SMTP server configuration
smtp_host = smtp.gmail.com
smtp_port = 587
smtp_user = your-email@gmail.com
smtp_password = your-app-password
smtp_use_tls = true
from_email = Beaver Habits <noreply@example.com>
from_name = Beaver Habits

[app]
# Root URL for generating verification and reset links
root_url = http://localhost:8000
# Whether email verification is required for new users
require_verification = true
# Email template settings
verification_subject = Please verify your Beaver Habits account
reset_subject = Reset your Beaver Habits password
```

**Email Features:**
- **User Registration**: New users receive verification emails
- **Email Verification**: Required before login (configurable)
- **Password Reset**: Users can request password reset via email
- **Development Mode**: Emails logged to console when SMTP not configured

**Available Routes:**
- `/gui/verify-email` - Email verification status and instructions
- `/gui/forgot-password` - Password reset request form  
- `/gui/reset-password` - Password reset form with token
- `/auth/verify?token=<token>` - API endpoint for email verification
- `/auth/forgot-password` - API endpoint for password reset requests
- `/auth/reset-password` - API endpoint for password reset

## Architecture

### Application Initialization Flow
1. `main.py` creates FastAPI app with lifespan management
2. Database tables created via `create_db_and_tables()` during startup
3. Three route initialization functions called:
   - `init_auth_routes()` - Sets up authentication endpoints
   - `init_api_routes()` - Registers API v1 endpoints
   - `init_gui_routes()` - Mounts NiceGUI app at `/gui`

### Backend Structure
- `beaverhabits/main.py`: FastAPI application entry point with lifespan management
- `beaverhabits/routes.py`: GUI route handlers and navigation logic
- `beaverhabits/app/`: Core application logic
  - `auth.py`: Authentication handlers (`user_authenticate`, `user_create_token`)
  - `crud.py`: Database operations (habits, lists, completions)
  - `db.py`: SQLAlchemy models and database setup
  - `users.py`: User management with FastAPI-Users (includes email sending hooks)
  - `dependencies.py`: FastAPI dependencies (`current_active_user`, `current_active_user_optional`)
- `beaverhabits/services/`: Business services
  - `email.py`: Email service for verification and password reset emails
- `beaverhabits/api/`: RESTful API endpoints
  - `routes/habits.py`: Habit completion endpoints
  - `routes/lists.py`: List management
  - `routes/export.py`: Data export functionality
- `beaverhabits/sql/models.py`: SQLAlchemy ORM models (Habit, List, HabitCompletion)

### Frontend Structure
- `beaverhabits/frontend/`: NiceGUI pages and components
  - `index_page.py`: Main habit tracker interface
  - `habit_page.py`: Individual habit view with calendar heatmap
  - `lists_page.py`: List management UI
  - `change_password_page.py`: Password change functionality
  - `verify_email_page.py`: Email verification status and instructions
  - `forgot_password_page.py`: Password reset request form
  - `reset_password_page.py`: Password reset form with token
  - `components/`: Reusable UI components
    - `layout/`: Page layout components (header, menu, navigation)
    - `index/`: Index page components (habit list, letter filter, week navigation)
    - `base.py`: Common UI components (buttons, links, grid)

### Routing Pattern
- Root `/` redirects to `/gui`
- GUI routes: `/gui/*` - Web interface endpoints
- API routes: `/api/v1/*` - RESTful API endpoints
- Auth routes: `/auth/*` - Authentication endpoints
- Health check: `/health`
- User count: `/users/count`

## Key Features to Understand

### List-Based Habit Organization
Habits can be organized into lists. The list filtering is handled via URL parameters:
- `?list=<id>` - Show habits from specific list
- `?list=None` - Show habits without a list
- No parameter - Show all habits
List state is persisted in `app.storage.user["current_list"]`

### Week Navigation
- Week offset tracked in `app.storage.user["week_offset"]`
- Navigation flag prevents automatic reset to current week
- `get_display_days()` returns 7 days based on current offset
- Week navigation UI component in center of header

### Letter Filtering
- Enabled via `settings.ENABLE_LETTER_FILTER`
- JavaScript-based filtering using `window.HabitFilter`
- Filters habits by first letter of name
- State managed client-side

### Authentication Flow
1. Users authenticate via `/login` with email/password
2. JWT token stored in `app.storage.user["auth_token"]`
3. AuthMiddleware automatically attaches token to requests
4. Protected routes use `Depends(current_active_user)`
5. Unrestricted pages: `/login`, `/register`

### State Management
- NiceGUI's `app.storage.user` for client-side state:
  - `auth_token`: JWT authentication token
  - `current_list`: Selected list ID
  - `week_offset`: Week navigation offset
  - `navigating`: Flag to prevent week reset
- List selection persisted across page loads

## API Authentication
All API endpoints require email/password in request body (not Bearer token). See API.md for detailed endpoint documentation including:
- `/api/v1/lists` - Get user lists
- `/api/v1/habits/{habit_id}/completions` - Update habit completions
- `/api/v1/export` - Export habit data

## Database
- Development uses SQLite by default (`.user/data.db`)
- Production typically uses PostgreSQL
- Database URL configured via environment or settings
- Async SQLAlchemy for all database operations
- Models in `sql/models.py`: User, Habit, List, HabitCompletion

## Important Patterns
1. All database operations are async - use `await` 
2. UI updates use NiceGUI's reactive system
3. Authentication required for all `/gui` routes except login/register
4. API endpoints handle their own authentication via email/password
5. List filtering happens at database level for performance
6. Use `logger` from `beaverhabits.logging` for consistent logging
7. Frontend components use `redirect()` helper for navigation within GUI mount path