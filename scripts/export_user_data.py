#!/usr/bin/env python
"""Export user data by email address without authentication."""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from beaverhabits.repositories import SQLAlchemyUnitOfWork
from beaverhabits.services.auth_service import AuthService
from beaverhabits.services.habit_service import HabitService
from beaverhabits.services.list_service import ListService


async def export_user_data(email: str) -> dict:
    """Export all data for a user identified by email."""
    async with SQLAlchemyUnitOfWork() as uow:
        # Find user
        auth_service = AuthService(uow)
        user = await auth_service.get_user_by_email(email)
        if not user:
            raise ValueError(f"User not found: {email}")

        habit_service = HabitService(uow)
        list_service = ListService(uow)

        # Get habits
        habits = await habit_service.get_user_habits(user)

        # Build export data
        data = {"habits": [], "lists": []}

        for habit in habits:
            records = await habit_service.get_habit_checks(habit.id, user)
            data["habits"].append({
                "id": habit.id,
                "name": habit.name,
                "order": habit.order,
                "weekly_goal": habit.weekly_goal,
                "list_id": habit.list_id,
                "records": [
                    {"day": r.day.isoformat(), "done": r.done, "text": r.text}
                    for r in records
                ]
            })

        # Get lists
        lists = await list_service.get_user_lists(user)
        data["lists"] = [
            {"id": l.id, "name": l.name, "order": l.order}
            for l in lists
        ]

        return data


def main():
    if len(sys.argv) != 2:
        print("Usage: python export_user_data.py <email>", file=sys.stderr)
        sys.exit(1)

    email = sys.argv[1]

    try:
        data = asyncio.run(export_user_data(email))
        print(json.dumps(data, indent=2))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
