"""
Migration 001: Add note and url fields to habits table.

This migration adds:
- note: TEXT field for habit descriptions (up to 2000 characters)
- url: VARCHAR(500) field for reference links
"""

from .base import ColumnMigration


class AddHabitNoteUrlFields(ColumnMigration):
    """Add note and url fields to the habits table."""

    def __init__(self):
        columns = [
            {
                'name': 'note',
                'type': 'TEXT',
                'description': 'Habit description note field'
            },
            {
                'name': 'url',
                'type': 'VARCHAR(500)',
                'description': 'Reference URL field'
            }
        ]
        super().__init__('habits', columns)

    def get_id(self) -> str:
        return '001_add_habit_note_url_fields'

    def get_description(self) -> str:
        return 'Add note and url fields to habits table'