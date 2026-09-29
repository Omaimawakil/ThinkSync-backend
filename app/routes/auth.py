import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import Token, UserCreate, UserOut
from app.services.auth_service import authenticate_user, create_user
from app.auth.security import create_access_token
from app.auth.dependencies import require_roles
from app.exceptions import ConflictError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning("Failed login attempt for username '%s'", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["user_id"], "role": user["role"]})
    logger.info("User '%s' logged in (role=%s)", user["user_id"], user["role"])
    return Token(access_token=token, role=user["role"], user_id=user["user_id"])


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, current_user: dict = Depends(require_roles("Admin"))):
    user = await create_user(
        username=payload.username,
        password=payload.password,
        role=payload.role,
        full_name=payload.full_name,
        department=payload.department,
    )
    if user is None:
        raise ConflictError("Username already exists")
    logger.info("Admin '%s' registered user '%s' (role=%s)",
                current_user.get("user_id"), payload.username, payload.role)
    return UserOut(**user)