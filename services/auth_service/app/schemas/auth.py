from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username", min_length=3)
    password: str = Field(..., description="Password", min_length=6)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "customer1",
                "password": "123456"
            }
        }

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_info: dict = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user_info": {
                    "customerId": "523K0000",
                    "username": "customer1",
                    "full_name": "Mr Customer 1",
                    "email": "customer1@example.com",
                    "phone_number": "0901234567",
                    "balance": 100000000.0
                }
            }
        }


class TokenData(BaseModel):
    customerId: Optional[str] = None
    username: Optional[str] = None


class ErrorResponse(BaseModel):
    status: str = Field(default="error", description="Response status")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Invalid credentials",
                "detail": "Username or password is incorrect"
            }
        }


class SuccessResponse(BaseModel):
    status: str = Field(default="success", description="Response status")
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {}
            }
        }
