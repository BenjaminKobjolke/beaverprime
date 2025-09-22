"""
Migration to add note and url fields to habits table.

This migration adds:
- note: Text field for habit description (up to 2000 characters)
- url: Text field for reference links (up to 500 characters)
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from beaverhabits.logging import logger


async def add_habit_note_url_fields(session: AsyncSession) -> None:
    """
    Add note and url fields to the habits table.

    This function adds the new fields to an existing database.
    """

    fields_to_add = [
        {
            'name': 'note',
            'type': 'TEXT',
            'nullable': True,
            'description': 'Habit description note field'
        },
        {
            'name': 'url',
            'type': 'VARCHAR(500)',
            'nullable': True,
            'description': 'Reference URL field'
        }
    ]

    try:
        for field in fields_to_add:
            # Check if column already exists
            check_column_sql = text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'habits'
                AND column_name = '{field['name']}'
                LIMIT 1
            """)

            result = await session.execute(check_column_sql)
            exists = result.fetchone()

            if exists:
                logger.info(f"[Migration] Column {field['name']} already exists in habits table")
                continue

            # Add the column
            add_column_sql = text(f"""
                ALTER TABLE habits
                ADD COLUMN {field['name']} {field['type']}
            """)

            await session.execute(add_column_sql)
            logger.info(f"[Migration] Added {field['name']} column to habits table ({field['description']})")

        await session.commit()
        logger.info("[Migration] Successfully added note and url fields to habits table")

    except Exception as e:
        logger.error(f"[Migration] Error adding fields to habits table: {e}")
        await session.rollback()
        raise


async def run_migration(session: AsyncSession) -> None:
    """
    Run the complete migration to add note and url fields.
    """
    logger.info("[Migration] Starting habit note and url fields migration")
    await add_habit_note_url_fields(session)
    logger.info("[Migration] Habit note and url fields migration completed")


if __name__ == "__main__":
    import asyncio
    from beaverhabits.app.db import get_async_session

    async def main():
        async with get_async_session() as session:
            await run_migration(session)

    asyncio.run(main())