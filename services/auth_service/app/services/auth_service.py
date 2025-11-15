from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..db.mongodb import get_users_collection
from ..core.security import verify_password, create_access_token, get_password_hash
from ..core.config import settings
from ..schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ErrorResponse,
    SuccessResponse,
    TokenData
)


class AuthService:
    """Authentication service for handling user authentication."""

    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
        users_collection = get_users_collection()
        
        # Find user by username
        user = await users_collection.find_one({"username": username})
        
        if not user:
            return None
        
        # Verify hashed password
        if not verify_password(password, user.get("password_hash", "")):
            return None
        
        return user

    @staticmethod
    def create_user_token(user: Dict[str, Any]) -> Dict[str, Any]:
        # Prepare token data with important information
        token_data = {
            "sub": user.get("username"),  # Subject (username)
            "customerId": user.get("customerId"),
            "username": user.get("username"),
            "email": user.get("email"),
        }
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        # Prepare user info
        user_info = {
            "customerId": user.get("customerId"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "phone_number": user.get("phone_number"),
            "balance": user.get("balance", 100000000.0)
        }
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            "user_info": user_info
        }

    @staticmethod
    async def login(username: str, password: str) -> Optional[Dict[str, Any]]:
        # Authenticate user
        user = await AuthService.authenticate_user(username, password)
        
        if not user:
            return None
        
        # Create and return token
        return AuthService.create_user_token(user)

    @staticmethod
    async def register(register_data: RegisterRequest) -> Optional[Dict[str, Any]]:
        """
        Register a new user.
        
        Args:
            register_data: Registration data including username, password, email, etc.
            
        Returns:
            User data with token if registration successful, None otherwise
        """
        users_collection = get_users_collection()
        
        # Validate passwords match
        if register_data.password != register_data.confirm_password:
            return None
        
        # Check if username already exists
        existing_user = await users_collection.find_one({"username": register_data.username})
        if existing_user:
            return None
        
        # Check if email already exists
        existing_email = await users_collection.find_one({"email": register_data.email})
        if existing_email:
            return None
        
        # Generate customerId (format: ST + timestamp suffix)
        customerId = f"ST{str(int(datetime.utcnow().timestamp()))[-6:]}"
        
        # Create new user document
        new_user = {
            "customerId": customerId,
            "username": register_data.username,
            "password_hash": get_password_hash(register_data.password),
            "full_name": register_data.full_name,
            "email": register_data.email,
            "phone_number": register_data.phone_number,
            "balance": 100000000.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert user into database
        result = await users_collection.insert_one(new_user)
        
        if not result.inserted_id:
            return None
        
        # Return the created user (without password_hash)
        created_user = await users_collection.find_one({"_id": result.inserted_id})
        
        # Create and return token for the new user
        return AuthService.create_user_token(created_user)
    
    @staticmethod
    async def deduct_balance(customer_id: str, amount: float) -> Optional[Dict[str, Any]]:
        """
        Deduct amount from customer's balance.
        
        Args:
            customer_id: Customer ID
            amount: Amount to deduct
            
        Returns:
            Updated user info if successful, None otherwise
        """
        users_collection = get_users_collection()
        
        # Find user by customerId
        user = await users_collection.find_one({"customerId": customer_id})
        
        if not user:
            return None
        
        current_balance = user.get("balance", 0.0)
        
        # Check if user has sufficient balance
        if current_balance < amount:
            return {
                "success": False,
                "message": f"Insufficient balance. Current: {current_balance}, Required: {amount}",
                "current_balance": current_balance,
                "required_amount": amount
            }
        
        # Deduct balance
        new_balance = current_balance - amount
        
        # Update user balance
        result = await users_collection.update_one(
            {"customerId": customer_id},
            {
                "$set": {
                    "balance": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            return None
        
        return {
            "success": True,
            "message": "Balance deducted successfully",
            "previous_balance": current_balance,
            "deducted_amount": amount,
            "new_balance": new_balance
        }
        