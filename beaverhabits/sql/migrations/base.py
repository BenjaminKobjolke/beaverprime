"""
Base migration classes and utilities.
"""

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional


class Migration(ABC):
    """Base class for database migrations."""

    def __init__(self):
        self.id: str = self.get_id()
        self.description: str = self.get_description()

    @abstractmethod
    def get_id(self) -> str:
        """Return unique migration ID (e.g., '001_add_habit_fields')."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return human-readable description of the migration."""
        pass

    @abstractmethod
    async def apply(self, session: AsyncSession) -> None:
        """Apply the migration."""
        pass

    async def can_apply(self, session: AsyncSession) -> bool:
        """
        Check if migration can be applied.
        Override this for complex migration conditions.
        """
        return True


class ColumnMigration(Migration):
    """Helper class for adding columns to tables."""

    def __init__(self, table_name: str, columns: list):
        """
        Initialize column migration.

        Args:
            table_name: Name of the table to modify
            columns: List of dicts with 'name', 'type', and 'description'
        """
        self.table_name = table_name
        self.columns = columns
        super().__init__()

    async def apply(self, session: AsyncSession) -> None:
        """Add columns to the specified table."""
        for column in self.columns:
            await self._add_column_if_not_exists(session, column)

    async def _add_column_if_not_exists(self, session: AsyncSession, column: dict) -> None:
        """Add a column if it doesn't already exist."""
        # Check if column exists
        check_sql = text(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{self.table_name}'
            AND COLUMN_NAME = '{column['name']}'
            LIMIT 1
        """)

        result = await session.execute(check_sql)
        exists = result.fetchone()

        if not exists:
            # Add the column
            add_sql = text(f"""
                ALTER TABLE {self.table_name}
                ADD COLUMN {column['name']} {column['type']}
            """)
            await session.execute(add_sql)
            print(f"[Migration] Added column {column['name']} to {self.table_name}")
        else:
            print(f"[Migration] Column {column['name']} already exists in {self.table_name}")

    async def can_apply(self, session: AsyncSession) -> bool:
        """Check if any columns need to be added."""
        for column in self.columns:
            check_sql = text(f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{self.table_name}'
                AND COLUMN_NAME = '{column['name']}'
                LIMIT 1
            """)

            result = await session.execute(check_sql)
            exists = result.fetchone()

            if not exists:
                return True  # At least one column needs to be added

        return False  # All columns already exist