"""
Authentication service layer for BeaverHabits application.

This service encapsulates business logic for user authentication and management,
using the repository pattern for data access.
"""

from typing import Optional
from uuid import UUID

from beaverhabits.app.auth import user_authenticate, user_create_token, user_check_token
from beaverhabits.logging import logger
from beaverhabits.repositories.interfaces import IUnitOfWork
from beaverhabits.sql.models import User


class AuthService:
    """Service for authentication and user management operations."""
    
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
    
    async def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """
        Authenticate a user and return an access token.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Access token if authentication successful, None otherwise
        """
        user = await user_authenticate(email, password)
        if user:
            token = await user_create_token(user)
            logger.info(f"[AuthService] User {email} authenticated successfully")
            return token
        
        logger.warning(f"[AuthService] Authentication failed for {email}")
        return None
    
    async def validate_token(self, token: str) -> bool:
        """
        Validate an access token.
        
        Args:
            token: The access token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        return await user_check_token(token)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get a user by their ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            The user if found, None otherwise
        """
        return await self._uow.users.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address.
        
        Args:
            email: The email address
            
        Returns:
            The user if found, None otherwise
        """
        return await self._uow.users.get_by_email(email)
    
    async def get_user_count(self) -> int:
        """
        Get the total number of users in the system.
        
        Returns:
            Total user count
        """
        return await self._uow.users.get_count()
    
    async def create_user(self, email: str, hashed_password: str, **kwargs) -> User:
        """
        Create a new user with business validation.
        
        Args:
            email: User email address
            hashed_password: The hashed password
            **kwargs: Additional user fields
            
        Returns:
            The created user
            
        Raises:
            ValueError: If validation fails
        """
        # Validate email format (basic check)
        if not email or "@" not in email:
            raise ValueError("Invalid email address")
        
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        user = await self._uow.users.create(
            email=email,
            hashed_password=hashed_password,
            **kwargs
        )
        
        await self._uow.commit()
        logger.info(f"[AuthService] Created user {email}")
        return user
    
    async def update_user(self, user_id: UUID, **updates) -> Optional[User]:
        """
        Update a user with business validation.
        
        Args:
            user_id: The user ID
            **updates: Fields to update
            
        Returns:
            The updated user if successful, None if not found
            
        Raises:
            ValueError: If validation fails
        """
        # Validate email if being updated
        if 'email' in updates and updates['email'] is not None:
            if not updates['email'] or "@" not in updates['email']:
                raise ValueError("Invalid email address")
            
            # Check if email is already in use by another user
            existing_user = await self.get_user_by_email(updates['email'])
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email address is already in use")
        
        user = await self._uow.users.update(user_id, **updates)
        if user:
            await self._uow.commit()
            logger.info(f"[AuthService] Updated user {user_id}")
        
        return user
    
    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """
        Change a user's password with validation.
        
        Args:
            user_id: The user ID
            current_password: Current password for verification
            new_password: New password (already hashed)
            
        Returns:
            True if password changed successfully, False otherwise
            
        Raises:
            ValueError: If validation fails
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        authenticated_user = await user_authenticate(user.email, current_password)
        if not authenticated_user:
            raise ValueError("Current password is incorrect")
        
        # Update password
        updated_user = await self.update_user(user_id, hashed_password=new_password)
        if updated_user:
            logger.info(f"[AuthService] Changed password for user {user_id}")
            return True
        
        return False