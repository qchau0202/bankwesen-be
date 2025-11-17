from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..db.mongodb import get_users_collection
from ..core.security import verify_password, create_access_token, get_password_hash
from ..core.config import settings
from ..schemas.auth import (
    LoginRequest,
    TokenResponse,
    ErrorResponse,
    SuccessResponse,
    TokenData
)

class AuthService:
    @staticmethod
    async def authenticateUserAsync(username: str, password: str) -> Optional[Dict[str, Any]]:
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
    def createUserToken(user: Dict[str, Any]) -> Dict[str, Any]:
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
    async def loginAsync(username: str, password: str) -> Optional[Dict[str, Any]]:
        # Authenticate user
        user = await AuthService.authenticateUserAsync(username, password)
        
        if not user:
            return None
        
        # Create and return token
        return AuthService.createUserToken(user)

    @staticmethod
    async def deductBalanceAsync(customer_id: str, amount: float) -> Optional[Dict[str, Any]]:
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
                    "balance": new_balance
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
        