from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
)
from fastapi.security import (
    HTTPBearer,
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import (
    RequestEmail,
    ResetPassword,
    UserResponse,
    UserModel,
    TokenModel,
)
from src.repository import users as user_repository
from src.services.auth import auth_service
from src.services.email import send_email, send_reset_password_email


router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBearer()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    body: UserModel,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    exist_user = await user_repository.get_user_by_email(
        body.email,
        db,
    )

    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists",
        )

    body.password = auth_service.get_password_hash(body.password)

    new_user = await user_repository.create_user(
        body,
        db,
    )

    background_tasks.add_task(
        send_email,
        new_user.email,
        new_user.username,
        request.base_url,
    )

    return {
        "user": new_user,
        "detail": (
            "User successfully created. "
            "Check your email confirmation"
        ),
    }


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = await user_repository.get_user_by_email(
        body.username,
        db,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email",
        )

    if not auth_service.verify_password(
        body.password,
        user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not confirmed",
        )

    access_token = await auth_service.create_access_token(
        data={"sub": user.email}
    )

    refresh_token = await auth_service.create_refresh_token(
        data={"sub": user.email}
    )

    await user_repository.update_token(
        user,
        refresh_token,
        db,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    email = await auth_service.decode_refresh_token(token)

    user = await user_repository.get_user_by_email(
        email,
        db,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if user.refresh_token != token:
        await user_repository.update_token(
            user,
            None,
            db,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = await auth_service.create_access_token(
        data={"sub": email}
    )

    new_refresh_token = await auth_service.create_refresh_token(
        data={"sub": email}
    )

    await user_repository.update_token(
        user,
        new_refresh_token,
        db,
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str,
    db: Session = Depends(get_db),
):
    email = await auth_service.get_email_from_token(token)

    user = await user_repository.get_user_by_email(
        email,
        db,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification error",
        )

    if user.confirmed:
        return {
            "message": "Your email is already confirmed",
        }

    await user_repository.confirmed_email(
        email,
        db,
    )

    return {
        "message": "Email confirmed",
    }


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user = await user_repository.get_user_by_email(
        body.email,
        db,
    )

    if user and user.confirmed:
        return {
            "message": "Your email is already confirmed",
        }

    if user:
        background_tasks.add_task(
            send_email,
            user.email,
            user.username,
            request.base_url,
        )

    return {
        "message": "Check your email for confirmation.",
    }


@router.post("/reset_password")
async def reset_password(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user = await user_repository.get_user_by_email(
        body.email,
        db,
    )

    if user:
        background_tasks.add_task(
            send_reset_password_email,
            user.email,
            user.username,
            request.base_url,
        )
    else:
        return {"message" : "A user with this email does not exist, please register."}


    return {
        "message": "Check your email to reset your password",
    }


@router.get("/reset_password/{token}")
async def reset_password_form(token: str):
    email = await auth_service.decode_reset_password_token(
        token
    )
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid or expired token'
        )

    return {
        "message": "Enter your new password",
        "email": email,
        "token": token,
    }


@router.post("/reset_password/confirm/{token}")
async def reset_password_confirm(
    token: str,
    body: ResetPassword,
    db: Session = Depends(get_db),
):
    email = await auth_service.decode_reset_password_token(
        token
    )

    user = await user_repository.get_user_by_email(
        email,
        db,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    hashed_password = auth_service.get_password_hash(
        body.password
    )

    user.password = hashed_password

    db.commit()

    return {
        "message": "Password successfully reset",
    }