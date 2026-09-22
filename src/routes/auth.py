
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
    """
    Registers a new user in the system.

    Checks whether a user with the specified email already exists,
    hashes the password, creates a new user in the database, and
    sends an email confirmation message in the background.

    :param body: The data required to create a new user.
    :type body: UserModel
    :param background_tasks: FastAPI background tasks for sending
        the confirmation email without blocking the response.
    :type background_tasks: BackgroundTasks
    :param request: The current HTTP request used to obtain the
        application base URL.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Information about the successfully created user.
    :rtype: UserResponse
    :raises HTTPException: 409 if a user with the specified email
        already exists.
    """

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
    """
    Authenticates a user and generates access and refresh tokens.

    The user's email and password are checked against the data
    stored in the database. The user must also have a confirmed
    email address. After successful authentication, new access
    and refresh tokens are generated and the refresh token is
    saved in the database.

    :param body: The OAuth2 form containing the user's email
        and password.
    :type body: OAuth2PasswordRequestForm
    :param db: The database session.
    :type db: Session
    :return: Access token, refresh token and token type.
    :rtype: TokenModel
    :raises HTTPException: 401 if the email is invalid.
    :raises HTTPException: 401 if the password is invalid.
    :raises HTTPException: 401 if the user's email is not confirmed.
    """

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
    """
    Refreshes the access and refresh tokens using a valid refresh token.

    The refresh token is extracted from the Authorization header,
    decoded and compared with the token stored for the current user.
    If the token is valid, new access and refresh tokens are generated
    and the old refresh token is replaced in the database.

    :param credentials: Authorization credentials containing the
        refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session.
    :type db: Session
    :return: New access token, refresh token and token type.
    :rtype: TokenModel
    :raises HTTPException: 401 if the refresh token is invalid,
        expired or does not match the stored token.
    """

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
    """
    Confirms a user's email address using a verification token.

    The token is decoded to retrieve the user's email address.
    The corresponding user is searched in the database. If the
    user exists and has not been confirmed yet, the email is
    marked as confirmed.

    :param token: The email verification token.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: A message indicating the email confirmation status.
    :rtype: dict
    :raises HTTPException: 400 if the verification token is invalid
        or the user cannot be found.
    """

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
    """
    Sends an email confirmation message to a registered user.

    If the user exists and their email is already confirmed,
    no new confirmation message is sent. Otherwise, the
    confirmation email is added to FastAPI background tasks.

    :param body: The request containing the user's email address.
    :type body: RequestEmail
    :param background_tasks: FastAPI background tasks used to send
        the confirmation email asynchronously.
    :type background_tasks: BackgroundTasks
    :param request: The current HTTP request used to obtain the
        application base URL.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: A message indicating that the confirmation email
        has been requested.
    :rtype: dict
    """

    user = await user_repository.get_user_by_email(
        body.email,
        db,
    )

    if user is None:
        return {
            }

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
    """
    Requests a password reset for a registered user.

    Searches for a user by email address. If the user exists,
    a password reset email containing a reset token is sent
    as a background task.

    :param body: The request containing the user's email address.
    :type body: RequestEmail
    :param background_tasks: FastAPI background tasks used to send
        the password reset email asynchronously.
    :type background_tasks: BackgroundTasks
    :param request: The current HTTP request used to obtain the
        application base URL.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: A message indicating that the password reset email
        has been requested, or an error message if the user
        does not exist.
    :rtype: dict
    """

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
        return {
            "message": (
                "A user with this email does not exist, "
                "please register."
            )
        }

    return {
        "message": "Check your email to reset your password",
    }


@router.get("/reset_password/{token}")
async def reset_password_form(token: str):
    """
    Validates a password reset token and returns data required
    to create a new password.

    The reset token is decoded to retrieve the email address
    associated with the password reset request.

    :param token: The password reset token received by the user.
    :type token: str
    :return: A message, user's email and the reset token.
    :rtype: dict
    :raises HTTPException: 400 if the token is invalid or expired.
    """

    email = await auth_service.decode_reset_password_token(
        token
    )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
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
    """
    Resets the user's password using a valid reset token.

    The reset token is decoded to identify the user. The new
    password is hashed and saved in the database.

    :param token: The password reset token.
    :type token: str
    :param body: The request containing the new password.
    :type body: ResetPassword
    :param db: The database session.
    :type db: Session
    :return: A message confirming that the password was changed.
    :rtype: dict
    :raises HTTPException: 404 if the user associated with the
        reset token does not exist.
    """

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

