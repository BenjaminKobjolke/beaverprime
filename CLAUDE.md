# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Beaver Prime Habit Tracker is a self-hosted habit tracking application built with FastAPI and NiceGUI. This fork adds enhanced features including list support, weekly goals, and a comprehensive API.

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

# Production mode
./start.bat  # or ./start.sh prd
```

### Testing
```bash
# Run tests with pytest
pytest

# Run specific test file
pytest tests/test_auth.py
```

## Architecture

### Backend Structure
- `beaverhabits/main.py`: FastAPI application entry point with lifespan management
- `beaverhabits/app/`: Core application logic
  - `auth.py`: Authentication handlers
  - `crud.py`: Database operations
  - `db.py`: SQLAlchemy models and database setup
  - `users.py`: User management with FastAPI-Users
- `beaverhabits/api/`: RESTful API endpoints
  - `routes/habits.py`: Habit completion endpoints
  - `routes/lists.py`: List management
  - `routes/export.py`: Data export functionality
- `beaverhabits/sql/`: Database models and migrations

### Frontend Structure
- `beaverhabits/frontend/`: NiceGUI pages and components
  - `index_page.py`: Main habit tracker interface
  - `habit_page.py`: Individual habit view
  - `lists_page.py`: List management UI
  - `change_password_page.py`: Password change functionality
  - `components/`: Reusable UI components organized by feature

### Routing Pattern
- GUI routes: `/gui/*` - Web interface endpoints
- API routes: `/api/v1/*` - RESTful API endpoints
- Auth routes: `/auth/*` - Authentication endpoints
- Static files served from `/statics/`

## Key Features to Understand

### List-Based Habit Organization
Habits can be organized into lists. The list filtering is handled via URL parameters:
- `?list=<id>` - Show habits from specific list
- `?list=None` - Show habits without a list
- No parameter - Show all habits

### Authentication Flow
1. Users authenticate via `/login` with email/password
2. JWT token stored in `app.storage.user["auth_token"]`
3. AuthMiddleware automatically attaches token to requests
4. Protected routes use `Depends(current_active_user)`

### State Management
- NiceGUI's `app.storage.user` for client-side state
- Week navigation state tracked to preserve position
- List selection persisted across page loads

## API Authentication
All API endpoints require email/password in request body (not Bearer token). See API.md for detailed endpoint documentation.

## Environment Variables
- `NICEGUI_STORAGE_PATH`: Storage location for NiceGUI data
- `LOGURU_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `UVICORN_LOG_LEVEL`: Uvicorn server log level
- `SENTRY_DSN`: Optional Sentry error tracking

## Database
- Development uses SQLite by default
- Production typically uses PostgreSQL
- Database URL configured via environment or settings
- Async SQLAlchemy for all database operations

## Important Patterns
1. All database operations are async - use `await` 
2. UI updates use NiceGUI's reactive system
3. Authentication required for all `/gui` routes except login/register
4. API endpoints handle their own authentication via email/password
5. List filtering happens at database level for performance