"""
Migration to add performance optimization indexes.

This migration adds the database indexes defined in the updated models
to improve query performance for frequently accessed data.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from beaverhabits.logging import logger


async def add_performance_indexes(session: AsyncSession) -> None:
    """
    Add performance optimization indexes to existing database.
    
    This function can be called to add the new indexes to an existing
    database without recreating tables.
    """
    
    indexes_to_create = [
        # HabitList indexes
        {
            'name': 'ix_lists_user_deleted_order',
            'table': 'lists',
            'columns': ['user_id', 'deleted', 'order'],
            'description': 'Optimize user lists queries with deleted filter'
        },
        
        # Habit indexes  
        {
            'name': 'ix_habits_user_list_deleted_order',
            'table': 'habits', 
            'columns': ['user_id', 'list_id', 'deleted', 'order'],
            'description': 'Optimize user habits by list queries'
        },
        {
            'name': 'ix_habits_user_deleted_order',
            'table': 'habits',
            'columns': ['user_id', 'deleted', 'order'], 
            'description': 'Optimize user habits queries without list filter'
        },
        {
            'name': 'ix_habits_id_user',
            'table': 'habits',
            'columns': ['id', 'user_id'],
            'description': 'Optimize habit lookups and updates'
        },
        
        # CheckedRecord indexes
        {
            'name': 'ix_checked_habit_day_done',
            'table': 'checked_records',
            'columns': ['habit_id', 'day', 'done'],
            'description': 'Optimize habit checks by date range and completion status'
        },
        {
            'name': 'ix_checked_habit_day', 
            'table': 'checked_records',
            'columns': ['habit_id', 'day'],
            'description': 'Optimize finding specific day records'
        },
        {
            'name': 'ix_checked_day_habit',
            'table': 'checked_records', 
            'columns': ['day', 'habit_id'],
            'description': 'Optimize date range queries'
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for index_info in indexes_to_create:
        try:
            # Check if index already exists
            check_sql = text(f"""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = :index_name
                LIMIT 1
            """)
            
            result = await session.execute(check_sql, {"index_name": index_info['name']})
            exists = result.fetchone() is not None
            
            if exists:
                logger.info(f"[Migration] Index {index_info['name']} already exists, skipping")
                skipped_count += 1
                continue
            
            # Create the index
            columns_sql = ', '.join(index_info['columns'])
            create_sql = text(f"""
                CREATE INDEX CONCURRENTLY {index_info['name']} 
                ON {index_info['table']} ({columns_sql})
            """)
            
            await session.execute(create_sql)
            await session.commit()
            
            logger.info(f"[Migration] Created index {index_info['name']}: {index_info['description']}")
            created_count += 1
            
        except Exception as e:
            logger.error(f"[Migration] Failed to create index {index_info['name']}: {e}")
            await session.rollback()
            continue
    
    logger.info(f"[Migration] Performance indexes migration completed: {created_count} created, {skipped_count} skipped")


async def add_unique_constraint_checked_records(session: AsyncSession) -> None:
    """
    Add unique constraint to checked_records to prevent duplicate habit-day entries.
    
    Note: This should be run carefully on existing data to ensure no duplicates exist.
    """
    
    try:
        # First, check for existing duplicates
        check_duplicates_sql = text("""
            SELECT habit_id, day, COUNT(*) as count
            FROM checked_records 
            GROUP BY habit_id, day
            HAVING COUNT(*) > 1
            LIMIT 5
        """)
        
        result = await session.execute(check_duplicates_sql)
        duplicates = result.fetchall()
        
        if duplicates:
            logger.warning(f"[Migration] Found {len(duplicates)} duplicate habit-day combinations. "
                          "Please clean up duplicates before adding unique constraint.")
            for dup in duplicates:
                logger.warning(f"  Duplicate: habit_id={dup.habit_id}, day={dup.day}, count={dup.count}")
            return
        
        # Check if constraint already exists
        check_constraint_sql = text("""
            SELECT 1 FROM information_schema.table_constraints 
            WHERE table_name = 'checked_records' 
            AND constraint_name = 'ix_checked_unique_habit_day'
            LIMIT 1
        """)
        
        result = await session.execute(check_constraint_sql)
        exists = result.fetchone() is not None
        
        if exists:
            logger.info("[Migration] Unique constraint ix_checked_unique_habit_day already exists")
            return
        
        # Create unique constraint
        create_constraint_sql = text("""
            CREATE UNIQUE INDEX CONCURRENTLY ix_checked_unique_habit_day 
            ON checked_records (habit_id, day)
        """)
        
        await session.execute(create_constraint_sql)
        await session.commit()
        
        logger.info("[Migration] Created unique constraint ix_checked_unique_habit_day")
        
    except Exception as e:
        logger.error(f"[Migration] Failed to create unique constraint: {e}")
        await session.rollback()


async def run_performance_migration(session: AsyncSession) -> None:
    """
    Run the complete performance optimization migration.
    
    This is the main function to call to apply all performance optimizations
    to an existing database.
    """
    logger.info("[Migration] Starting performance optimization migration")
    
    # Add performance indexes
    await add_performance_indexes(session)
    
    # Add unique constraint (optional, requires clean data)
    await add_unique_constraint_checked_records(session)
    
    logger.info("[Migration] Performance optimization migration completed")


# Helper function for manual execution
async def manual_migration():
    """
    Helper function to manually run the migration.
    
    Usage:
        from beaverhabits.sql.migrations.add_performance_indexes import manual_migration
        await manual_migration()
    """
    from beaverhabits.app.db import get_async_session
    
    async for session in get_async_session():
        await run_performance_migration(session)
        break