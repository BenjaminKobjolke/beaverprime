# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Beaver Prime Habit Tracker is a self-hosted habit tracking application built with FastAPI and NiceGUI. This fork adds enhanced features including list support, weekly goals, letter filtering, internationalization, and a comprehensive API.

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
from_email = BeaverPrime <noreply@example.com>
from_name = BeaverPrime

[app]
# Root URL for generating verification and reset links
root_url = http://localhost:8000
# Whether email verification is required for new users
require_verification = true
# Email template settings
verification_subject = Please verify your BeaverPrime account
reset_subject = Reset your BeaverPrime password
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

**Native App Integration:**

- Email verification success page detects `beaverprime://` URL scheme support
- Automatically redirects to native Android app when available
- Falls back to web app when native app is not installed
- Uses JavaScript-based detection with iframe and window.location attempts

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
  - `i18n.py`: Internationalization service with translation management
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
  - `settings_page.py`: User settings page (language, display, password, import/export)
  - `change_password_page.py`: Password change functionality
  - `verify_email_page.py`: Email verification status and instructions
  - `forgot_password_page.py`: Password reset request form
  - `reset_password_page.py`: Password reset form with token
  - `components/`: Reusable UI components
    - `layout/`: Page layout components (header, menu, navigation)
    - `index/`: Index page components (habit list, letter filter, week navigation)
    - `habit/`: Habit-specific components
      - `goal.py`: `HabitGoalLabel` and `HabitConsecutiveWeeksLabel` components
      - `inputs.py`: `MultiPartNameInput` with dynamic add/remove functionality
      - `buttons.py`: Habit action buttons (save, delete, add)
    - `base.py`: Common UI components (buttons, links, grid)

### Routing Pattern

- Root `/` redirects to `/gui`
- GUI routes: `/gui/*` - Web interface endpoints
- API routes: `/api/v1/*` - RESTful API endpoints
- Auth routes: `/auth/*` - Authentication endpoints
- Settings route: `/gui/settings` - User preferences and data management
- Health check: `/health`
- User count: `/users/count`

## Key Features to Understand

### List-Based Habit Organization

Habits can be organized into lists. The list filtering is handled via URL parameters:

- `?list=<id>` - Show habits from specific list
- `?list=None` - Show habits without a list
- No parameter - Show all habits
  List state is persisted in `app.storage.user["current_list"]`

### Multi-Part Habit Names

- Habits support multi-part names using "||" separator (e.g., "Exercise || Walk 30 minutes")
- `MultiPartNameInput` component allows adding/removing subparts with "+" and "-" buttons
- UI dynamically adds/removes input fields for each habit part
- Combined name stored as single string with "||" delimiter

### Week Navigation

- Week offset tracked in `app.storage.user["week_offset"]`
- Navigation flag prevents automatic reset to current week
- `get_display_days()` returns 7 days based on current offset
- Week navigation UI component in center of header

### Consecutive Weeks Display

- Shows how many consecutive weeks a habit goal has been met (e.g., "3w")
- Calculated by `get_consecutive_weeks_count()` in `utils.py`
- Algorithm:
  - Starts from previous week (skips current incomplete week)
  - Counts backwards until first week that doesn't meet goal
  - Bonus: Adds current week if it already meets the goal
- Display controlled by `settings.INDEX_SHOW_CONSECUTIVE_WEEKS`
- Configurable via GUI settings page under "Display Settings"
- Positioned below weekly goal label ("5x") in smaller, muted font

### Letter Filtering

- Enabled via `settings.ENABLE_LETTER_FILTER`
- JavaScript-based filtering using `window.HabitFilter`
- Filters habits by first letter of name
- State managed client-side

### Internationalization (i18n)

- Translation files stored in `statics/lang/` as JSON files (en.json, de.json, etc.)
- Translation service in `beaverhabits/services/i18n.py` with dot notation key lookup
- `t("key.subkey")` function for translations with variable substitution support
- Language persistence in `app.storage.user["language"]`
- Language switcher components for auth pages and main interface
- Email templates support internationalization via translation service
- Currently supports English and German with extensible architecture

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
  - `language`: User's selected language code
- List selection persisted across page loads

### Settings and Data Management

- Centralized settings page at `/gui/settings` with four main sections:
  - **Language Settings**: Switch between available languages with live preview
  - **Display Settings**: Configure UI display options including consecutive weeks visibility
  - **Password Management**: Change user password with validation
  - **Data Management**: Import/export functionality with comprehensive options
- Export creates JSON files with habits, lists, and completion history
- Import supports merging with existing data or clearing all existing data first
- Bulk operations for data clearing using `delete_all_user_habits()` and `delete_all_user_lists()`

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
- Bulk operations available: `delete_all_user_habits()`, `delete_all_user_lists()`

## Important Patterns

1. All database operations are async - use `await`
2. UI updates use NiceGUI's reactive system
3. Authentication required for all `/gui` routes except login/register
4. API endpoints handle their own authentication via email/password
5. List filtering happens at database level for performance
6. Use `logger` from `beaverhabits.logging` for consistent logging
7. Frontend components use `redirect()` helper for navigation within GUI mount path
8. Use `t("translation.key")` for all user-facing text to support internationalization
9. Initialize user language with `init_user_language()` before rendering UI components
10. Multi-part habit names use "||" separator for storage and `MultiPartNameInput` for editing
11. Consecutive weeks calculation starts from previous week to avoid current week bias

## Configuration Settings

Key settings that control application behavior:

### Display Settings
- `INDEX_SHOW_CONSECUTIVE_WEEKS`: Controls consecutive weeks display (default: True)
- `INDEX_SHOW_HABIT_COUNT`: Show habit completion counts (default: False)  
- `INDEX_SHOW_PRIORITY`: Show habit priority indicators (default: False)
- `ENABLE_LETTER_FILTER`: Enable letter-based habit filtering (default: True)

### UI Layout
- `INDEX_HABIT_NAME_COLUMNS`: Width allocation for habit names (default: 8)
- `INDEX_HABIT_DATE_COLUMNS`: Date column configuration (default: -1 for week view)

### Features
- `ENABLE_HABIT_NOTES`: Enable habit notes functionality (default: False)

Settings can be configured in `configs.py` or via the `/gui/settings` page for user preferences.
