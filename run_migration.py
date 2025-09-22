#!/usr/bin/env python3
"""
Script to run the habit note and URL fields migration.
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from beaverhabits.app.db import get_async_session
from beaverhabits.sql.migrations.add_habit_note_url_fields import run_migration


async def main():
    """Run the migration."""
    async with get_async_session() as session:
        await run_migration(session)
        print("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())