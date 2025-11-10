from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.auth import LoginRequest, TokenResponse, ErrorResponse, SuccessResponse, TokenData
from ..services.auth_service import AuthService
from ..core.dependencies import get_current_user, require_admin, require_staff

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


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
            "description": "Invalid credentials",
            "model": ErrorResponse
        }
    },
    summary="User Login",
    description="Authenticate user and return JWT access token with user information"
)
async def login(login_data: LoginRequest):
    """
    Login endpoint for user authentication.
    
    **Request Body:**
    - **username**: User's username (minimum 3 characters)
    - **password**: User's password (minimum 6 characters)
    
    **Response:**
    - **access_token**: JWT token for authentication
    - **token_type**: Always "bearer"
    - **expires_in**: Token expiration time in seconds
    - **user_info**: User information (userid, username, role, full_name, email, balance)
    
    **Roles:**
    - student: Regular student user
    - staff: Staff member with elevated privileges
    - admin: Administrator with full access
    """
    # Attempt login
    result = await AuthService.login(login_data.username, login_data.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
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
    """
    Get current user information from JWT token.
    Requires valid authentication token.
    """
    return SuccessResponse(
        status="success",
        message="User information retrieved successfully",
        data={
            "userid": current_user.userid,
            "username": current_user.username,
            "role": current_user.role,
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
    """
    Verify JWT token validity.
    Returns user information if token is valid.
    """
    return SuccessResponse(
        status="success",
        message="Token is valid",
        data={
            "userid": current_user.userid,
            "username": current_user.username,
            "role": current_user.role,
            "is_valid": True
        }
    )


@router.get(
    "/admin/users",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get All Users (Admin Only)",
    description="Get list of all users - accessible only by administrators"
)
async def get_all_users(current_user: TokenData = Depends(require_admin)):
    """
    Protected endpoint - Only accessible by admin role.
    Example of role-based access control for internal APIs.
    """
    return SuccessResponse(
        status="success",
        message="Admin access granted",
        data={
            "requested_by": current_user.username,
            "role": current_user.role,
            "note": "This endpoint is only accessible by administrators"
        }
    )


@router.get(
    "/staff/dashboard",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Staff Dashboard (Staff/Admin Only)",
    description="Access staff dashboard - accessible by staff and administrators"
)
async def staff_dashboard(current_user: TokenData = Depends(require_staff)):
    """
    Protected endpoint - Only accessible by staff and admin roles.
    Example of role-based access control for internal APIs.
    """
    return SuccessResponse(
        status="success",
        message="Staff access granted",
        data={
            "requested_by": current_user.username,
            "role": current_user.role,
            "note": "This endpoint is accessible by staff and administrators"
        }
    )
