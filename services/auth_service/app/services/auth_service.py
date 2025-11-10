from typing import Optional, Dict, Any
from datetime import timedelta
from ..db.mongodb import get_users_collection
from ..core.security import verify_password, create_access_token
from ..core.config import settings


class AuthService:
    """Authentication service for handling user authentication."""

    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: User's username
            password: User's plain password
            
        Returns:
            User data if authentication successful, None otherwise
        """
        users_collection = get_users_collection()
        
        # Find user by username
        user = await users_collection.find_one({"username": username})
        
        if not user:
            return None
        
        # Compare plain password (TEMPORARY: not secure, will hash later)
        if password != user.get("password", ""):
            return None
        
        return user

    @staticmethod
    def create_user_token(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a JWT token for an authenticated user.
        
        Args:
            user: User data from database
            
        Returns:
            Dictionary containing token and user information
        """
        # Prepare token data with important information
        token_data = {
            "sub": user.get("username"),  # Subject (username)
            "userid": user.get("userid"),
            "username": user.get("username"),
            "role": user.get("role"),
            "email": user.get("email")
        }
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        # Prepare user info (without sensitive data)
        user_info = {
            "userid": user.get("userid"),
            "username": user.get("username"),
            "role": user.get("role"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "balance": user.get("balance", 0.0)
        }
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            "user_info": user_info
        }

    @staticmethod
    async def login(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Login a user and return token.
        
        Args:
            username: User's username
            password: User's plain password
            
        Returns:
            Token data if login successful, None otherwise
        """
        # Authenticate user
        user = await AuthService.authenticate_user(username, password)
        
        if not user:
            return None
        
        # Create and return token
        return AuthService.create_user_token(user)
