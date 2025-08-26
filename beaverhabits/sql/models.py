import datetime
from typing import List
from uuid import UUID, uuid4
from sqlalchemy import ForeignKey, func, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from .database import Base

class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps"""
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), insert_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), insert_default=func.now(), onupdate=func.now()
    )

class User(TimestampMixin, SQLAlchemyBaseUserTableUUID, Base):
    """User model with relationships to habits and lists"""
    __tablename__ = "users"

    habits: Mapped[List["Habit"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    lists: Mapped[List["HabitList"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class HabitList(TimestampMixin, Base):
    """List model for organizing habits"""
    __tablename__ = "lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(default=0)
    deleted: Mapped[bool] = mapped_column(default=False)
    enable_letter_filter: Mapped[bool] = mapped_column(default=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    user: Mapped["User"] = relationship(back_populates="lists")
    habits: Mapped[List["Habit"]] = relationship(
        back_populates="habit_list", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Composite index for user lists queries (most common)
        Index('ix_lists_user_deleted_order', 'user_id', 'deleted', 'order'),
    )

class Habit(TimestampMixin, Base):
    """Habit model with checked records"""
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(default=0)
    weekly_goal: Mapped[int | None] = mapped_column(default=0)
    deleted: Mapped[bool] = mapped_column(default=False)
    star: Mapped[bool] = mapped_column(default=False)
    list_id: Mapped[int | None] = mapped_column(ForeignKey("lists.id"), index=True, nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    user: Mapped["User"] = relationship(back_populates="habits")
    habit_list: Mapped["HabitList"] = relationship(back_populates="habits")
    checked_records: Mapped[List["CheckedRecord"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Most common query: user habits by list and deleted status
        Index('ix_habits_user_list_deleted_order', 'user_id', 'list_id', 'deleted', 'order'),
        # Query for habits without list (list_id IS NULL)
        Index('ix_habits_user_deleted_order', 'user_id', 'deleted', 'order'),
        # For habit lookup and updates
        Index('ix_habits_id_user', 'id', 'user_id'),
    )

class CheckedRecord(TimestampMixin, Base):
    """Record of habit completion status for a specific day"""
    __tablename__ = "checked_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    day: Mapped[datetime.date] = mapped_column(nullable=False)
    done: Mapped[bool] = mapped_column(default=False)
    text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"), index=True)

    habit: Mapped["Habit"] = relationship(back_populates="checked_records")

    __table_args__ = (
        # Most critical: habit checks by date range (for streak calculations)
        Index('ix_checked_habit_day_done', 'habit_id', 'day', 'done'),
        # For finding specific day's record
        Index('ix_checked_habit_day', 'habit_id', 'day'),
        # For date range queries (weekly, monthly views)
        Index('ix_checked_day_habit', 'day', 'habit_id'),
        # Ensure unique habit-day combination
        Index('ix_checked_unique_habit_day', 'habit_id', 'day', unique=True),
    )
