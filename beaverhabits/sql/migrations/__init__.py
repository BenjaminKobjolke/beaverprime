"""
Database migration system for BeaverHabits.

This module provides a proper migration tracking system that ensures
migrations run exactly once and provides an audit trail.
"""

from .migration_runner import run_all_migrations

__all__ = ['run_all_migrations']