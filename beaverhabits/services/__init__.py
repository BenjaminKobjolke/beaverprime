"""
Service layer for BeaverHabits application.

This package provides business logic services that operate on domain entities
using the repository pattern for data access.
"""

# Import only the email service which is needed by existing code
from .email import EmailService, email_service

# Import performance services
from .cache_service import habit_calculation_cache, general_cache, start_cache_cleanup, stop_cache_cleanup
from .performance_service import PerformanceService

# Lazy import other services to avoid circular dependencies
def get_auth_service():
    from .auth_service import AuthService
    return AuthService

def get_habit_service():
    from .habit_service import HabitService
    return HabitService

def get_list_service():
    from .list_service import ListService
    return ListService

__all__ = [
    'EmailService',
    'email_service',
    'get_auth_service',
    'get_habit_service', 
    'get_list_service',
    'PerformanceService',
    'habit_calculation_cache',
    'general_cache',
    'start_cache_cleanup',
    'stop_cache_cleanup',
]