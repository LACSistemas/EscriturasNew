"""FastAPI Authentication routes"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from models.schemas import LoginRequest, LoginResponse, MessageResponse, AuthStatusResponse
from auth import authenticate_user

router = APIRouter(tags=["authentication"])


def get_session(request: Request):
    """Get session from request"""
    return request.session


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, request: Request):
    """Login endpoint"""
    try:
        user = authenticate_user(credentials.username, credentials.password)
        if user:
            request.session['user'] = user['username']
            request.session['authenticated'] = True
            request.session['user_data'] = user
            return LoginResponse(
                success=True,
                message="Login successful",
                user={"username": credentials.username}
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request):
    """Logout endpoint"""
    request.session.pop('user', None)
    request.session.pop('authenticated', None)
    return MessageResponse(success=True, message="Logout successful")


@router.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status(request: Request):
    """Check authentication status"""
    authenticated = request.session.get('authenticated', False)
    user = request.session.get('user')

    if authenticated and user:
        return AuthStatusResponse(
            authenticated=True,
            user={"username": user}
        )
    else:
        return AuthStatusResponse(authenticated=False, user=None)
