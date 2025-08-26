"""
Repository pattern implementation for BeaverHabits.

This package provides abstract interfaces and concrete implementations
for data access operations, following the Repository pattern to separate
business logic from data access concerns.
"""

from .interfaces import IHabitRepository, IListRepository, IUserRepository, IUnitOfWork
from .sqlalchemy_repositories import (
    SQLAlchemyHabitRepository,
    SQLAlchemyListRepository, 
    SQLAlchemyUserRepository,
    SQLAlchemyUnitOfWork
)

__all__ = [
    # Interfaces
    'IHabitRepository',
    'IListRepository', 
    'IUserRepository',
    'IUnitOfWork',
    # Implementations
    'SQLAlchemyHabitRepository',
    'SQLAlchemyListRepository',
    'SQLAlchemyUserRepository', 
    'SQLAlchemyUnitOfWork',
]