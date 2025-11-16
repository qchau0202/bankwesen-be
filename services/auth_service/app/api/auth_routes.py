from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ErrorResponse,
    SuccessResponse,
    TokenData
)
from ..services.auth_service import AuthService
from ..core.dependencies import (
    get_current_user,
    verify_api_key
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Login successful",
            "model": TokenResponse
        },
        401: {
            "description": "Invalid credentials or missing API key",
            "model": ErrorResponse
        },
        403: {
            "description": "Invalid API key",
            "model": ErrorResponse
        }
    },
    summary="User Login",
    description="Authenticate user and return JWT access token with user information. Requires valid API key in X-API-Key header."
)
async def login(
    login_data: LoginRequest,
    api_key: str = Depends(verify_api_key)
):
    # Attempt login
    result = await AuthService.loginAsync(login_data.username, login_data.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenResponse(**result)

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "User registered successfully",
            "model": TokenResponse
        },
        400: {
            "description": "Bad request - passwords don't match",
            "model": ErrorResponse
        },
        401: {
            "description": "Missing or invalid API key",
            "model": ErrorResponse
        },
        403: {
            "description": "Invalid API key",
            "model": ErrorResponse
        },
        409: {
            "description": "User already exists",
            "model": ErrorResponse
        }
    },
    summary="User Registration",
    description="Register a new user account and return JWT access token. Requires valid API key in X-API-Key header."
)
async def register(
    register_data: RegisterRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Register a new user with the following validations:
    - Username must be unique
    - Email must be unique
    - Passwords must match
    - Password will be hashed before storing
    
    Returns a JWT token upon successful registration.
    """
    # Validate passwords match
    if register_data.password != register_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    # Attempt registration
    result = await AuthService.registerAsync(register_data)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )
    
    return TokenResponse(**result)

@router.get(
    "/me",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get information about the currently authenticated user"
)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    return SuccessResponse(
        status="success",
        message="User information retrieved successfully",
        data={
            "customerId": current_user.customerId,
            "username": current_user.username,
        }
    )


@router.get(
    "/verify",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Token",
    description="Verify if the provided token is valid"
)
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    return SuccessResponse(
        status="success",
        message="Token is valid",
        data={
            "customerId": current_user.customerId,
            "username": current_user.username,
            "is_valid": True
        }
    )






