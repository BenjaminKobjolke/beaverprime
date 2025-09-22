"""
Migration runner for database schema changes.

This module handles the execution and tracking of database migrations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Set
from .base import Migration

# Import all migrations here
from .m001_add_habit_note_url_fields import AddHabitNoteUrlFields


async def ensure_migrations_table_exists(session: AsyncSession) -> None:
    """Create the migrations tracking table if it doesn't exist."""
    try:
        # Try to query the table to see if it exists
        await session.execute(text("SELECT 1 FROM migrations LIMIT 1"))
        print("[Migration] Migrations table already exists")
    except Exception:
        # Table doesn't exist, create it
        create_table_sql = text("""
            CREATE TABLE migrations (
                id VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await session.execute(create_table_sql)
        await session.commit()
        print("[Migration] Created migrations tracking table")


async def get_applied_migrations(session: AsyncSession) -> Set[str]:
    """Get the set of migration IDs that have been applied."""
    try:
        result = await session.execute(text("SELECT id FROM migrations"))
        applied = {row[0] for row in result.fetchall()}
        print(f"[Migration] Found {len(applied)} previously applied migrations")
        return applied
    except Exception as e:
        print(f"[Migration] Error getting applied migrations: {e}")
        return set()


async def record_migration_applied(session: AsyncSession, migration_id: str) -> None:
    """Record that a migration has been successfully applied."""
    insert_sql = text("INSERT INTO migrations (id) VALUES (:migration_id)")
    await session.execute(insert_sql, {"migration_id": migration_id})
    await session.commit()
    print(f"[Migration] Recorded migration {migration_id} as applied")


def get_all_migrations() -> List[Migration]:
    """Get all available migrations in order."""
    migrations = [
        AddHabitNoteUrlFields(),
        # Add new migrations here in order
    ]

    # Sort by ID to ensure consistent ordering
    migrations.sort(key=lambda m: m.id)
    return migrations


async def run_all_migrations(session: AsyncSession) -> None:
    """Run all pending migrations."""
    print("[Migration] Starting migration runner")

    # Step 1: Ensure migrations table exists
    await ensure_migrations_table_exists(session)

    # Step 2: Get applied migrations
    applied_migrations = await get_applied_migrations(session)

    # Step 3: Get all available migrations
    all_migrations = get_all_migrations()
    print(f"[Migration] Found {len(all_migrations)} total migrations")

    # Step 4: Run unapplied migrations
    pending_count = 0
    for migration in all_migrations:
        if migration.id not in applied_migrations:
            print(f"[Migration] Running migration: {migration.id} - {migration.description}")

            # Check if migration can be applied
            if await migration.can_apply(session):
                try:
                    await migration.apply(session)
                    await session.commit()
                    await record_migration_applied(session, migration.id)
                    pending_count += 1
                    print(f"[Migration] Successfully applied: {migration.id}")
                except Exception as e:
                    print(f"[Migration] Failed to apply {migration.id}: {e}")
                    await session.rollback()
                    raise
            else:
                # Migration conditions not met (e.g., columns already exist)
                # Mark as applied without running
                await record_migration_applied(session, migration.id)
                print(f"[Migration] Marked {migration.id} as applied (no changes needed)")
        else:
            print(f"[Migration] Skipping already applied migration: {migration.id}")

    if pending_count > 0:
        print(f"[Migration] Applied {pending_count} new migrations")
    else:
        print("[Migration] No pending migrations")

    print("[Migration] Migration runner completed")