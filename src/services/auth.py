
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import uuid4


import pickle
import redis
import bcrypt

from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import settings


class Auth:
    """
    Provides authentication and authorization functionality.

    The class is responsible for password hashing and verification,
    creation and validation of JWT access, refresh, email confirmation
    and password reset tokens, as well as retrieving the current user.
    """

    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm

    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="/api/auth/login"
    )

    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
    )

    @staticmethod
    def verify_password(
        plain_password: str,
        hashed_password: str,
    ):
        """
        Verifies a plain-text password against a hashed password.

        The plain password is encoded into bytes and compared with
        the stored bcrypt password hash.

        :param plain_password: The password provided by the user.
        :type plain_password: str
        :param hashed_password: The bcrypt hash stored in the database.
        :type hashed_password: str
        :return: True if the password matches the hash, otherwise False.
        :rtype: bool
        """

        password_bytes = plain_password.encode("utf-8")
        hashed_password_bytes = hashed_password.encode("utf-8")

        return bcrypt.checkpw(
            password_bytes,
            hashed_password_bytes,
        )

    @staticmethod
    def get_password_hash(password: str):
        """
        Creates a secure bcrypt hash for a password.

        A new random salt is generated for each password before
        hashing it with bcrypt.

        :param password: The plain-text password to hash.
        :type password: str
        :return: The bcrypt hash of the password.
        :rtype: str
        """

        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()

        return bcrypt.hashpw(
            password_bytes,
            salt,
        ).decode("utf-8")

    async def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[float] = None,
    ):
        """
        Creates a JWT access token.

        The token contains the provided data, issue time,
        expiration time and the access token scope. By default,
        the access token is valid for 15 minutes.

        :param data: Data that will be stored inside the JWT payload.
        :type data: dict
        :param expires_delta: Custom token lifetime in seconds.
            If not specified, the token is valid for 15 minutes.
        :type expires_delta: Optional[float]
        :return: Encoded JWT access token.
        :rtype: str
        """

        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + timedelta(
                seconds=expires_delta
            )
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=15
            )

        to_encode.update(
            {
                "jti": str(uuid4()),
                "iat": datetime.utcnow(),
                "exp": expire,
                "scope": "access_token",
            }
        )

        encode_access_token = jwt.encode(
            to_encode,
            self.SECRET_KEY,
            algorithm=self.ALGORITHM,
        )

        return encode_access_token

    async def create_refresh_token(
        self,
        data: dict,
        expires_delta: Optional[float] = None,
    ):
        """
        Creates a JWT refresh token.

        The token contains the provided data, issue time,
        expiration time and the refresh token scope. By default,
        the refresh token is valid for 7 days.

        :param data: Data that will be stored inside the JWT payload.
        :type data: dict
        :param expires_delta: Custom token lifetime in seconds.
            If not specified, the token is valid for 7 days.
        :type expires_delta: Optional[float]
        :return: Encoded JWT refresh token.
        :rtype: str
        """

        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + timedelta(
                seconds=expires_delta
            )
        else:
            expire = datetime.utcnow() + timedelta(
                days=7
            )

        to_encode.update(
            {
                "jti": str(uuid4()),
                "iat": datetime.utcnow(),
                "exp": expire,
                "scope": "refresh_token",
            }
        )

        encode_refresh_token = jwt.encode(
            to_encode,
            self.SECRET_KEY,
            algorithm=self.ALGORITHM,
        )

        return encode_refresh_token

    async def decode_refresh_token(
        self,
        refresh_token: str,
    ):
        """
        Decodes and validates a JWT refresh token.

        The method verifies the token signature and checks whether
        the token has the required refresh token scope. If the token
        is valid, the user's email is returned.

        :param refresh_token: The JWT refresh token to validate.
        :type refresh_token: str
        :return: The email address stored in the token.
        :rtype: str
        :raises HTTPException: 401 if the token is invalid, expired,
            or has an incorrect scope.
        """

        try:
            payload = jwt.decode(
                refresh_token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM],
            )

            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not valide credentials",
            )

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
    ):
        """
        Retrieves the currently authenticated user.

        The access token is decoded and validated first. If the token
        contains a valid access token scope, the user's email is
        extracted from it. The user is then searched in Redis cache.
        If the user is not found in the cache, the database is queried
        and the user is saved to Redis for subsequent requests.

        :param token: The OAuth2 access token provided by the client.
        :type token: str
        :param db: The database session.
        :type db: Session
        :return: The authenticated user.
        :rtype: User
        :raises HTTPException: 401 if the access token is invalid,
            expired, has an incorrect scope, or the user cannot be found.
        """

        credentials_exeption = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM],
            )

            if payload["scope"] == "access_token":
                email = payload.get("sub")

                if email is None:
                    raise credentials_exeption
            else:
                raise credentials_exeption

        except JWTError:
            raise credentials_exeption

        user = self.r.get(f"user:{email}")

        if user is None:
            user = await repository_users.get_user_by_email(
                email,
                db,
            )

            if user is None:
                raise credentials_exeption

            self.r.set(
                f"user:{email}",
                pickle.dumps(user),
            )

            self.r.expire(
                f"user:{email}",
                900,
            )
        else:
            user = pickle.loads(user)

        return user

    async def create_email_token(
        self,
        data: dict,
    ):
        """
        Creates a JWT token for email confirmation.

        The token contains the provided data, issue time and
        expiration time. By default, the email confirmation token
        is valid for 7 days.

        :param data: Data that will be stored inside the JWT payload.
        :type data: dict
        :return: Encoded JWT email confirmation token.
        :rtype: str
        """

        to_encode = data.copy()

        expire = datetime.utcnow() + timedelta(
            days=7
        )

        to_encode.update(
            {
                "iat": datetime.utcnow(),
                "exp": expire,
            }
        )

        token = jwt.encode(
            to_encode,
            self.SECRET_KEY,
            algorithm=self.ALGORITHM,
        )

        return token

    async def get_email_from_token(
        self,
        token: str,
    ):
        """
        Extracts a user's email address from an email confirmation token.

        The JWT token is decoded and the email address stored in
        the `sub` field is returned.

        :param token: The email confirmation token.
        :type token: str
        :return: The email address stored in the token.
        :rtype: str
        :raises HTTPException: 422 if the token is invalid or cannot
            be decoded.
        """

        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM],
            )

            email = payload["sub"]

            return email

        except JWTError as e:
            print(e)

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid token for email",
            )

    async def create_reset_password_token(
        self,
        data: dict,
    ):
        """
        Creates a JWT token for password reset.

        The token contains the provided data, issue time,
        expiration time and a specific token type that identifies
        it as a password reset token. By default, the token is
        valid for 15 minutes.

        :param data: Data that will be stored inside the JWT payload.
        :type data: dict
        :return: Encoded JWT password reset token.
        :rtype: str
        """

        to_encode = data.copy()

        expire = datetime.utcnow() + timedelta(
            minutes=15
        )

        to_encode.update(
            {
                "iat": datetime.utcnow(),
                "exp": expire,
                "type": "reset_password",
            }
        )

        token = jwt.encode(
            to_encode,
            self.SECRET_KEY,
            algorithm=self.ALGORITHM,
        )

        return token

    async def decode_reset_password_token(
        self,
        token: str,
    ):
        """
        Decodes and validates a password reset token.

        The method verifies the JWT signature and checks the token
        type to ensure that it was created specifically for
        password reset operations. If the token is valid, the
        user's email address is returned.

        :param token: The password reset token.
        :type token: str
        :return: The email address stored in the reset token.
        :rtype: str
        :raises HTTPException: 401 if the token is invalid, expired,
            or does not have the required reset password type.
        """

        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )

            email = payload.get("sub")
            token_type = payload.get("type")

            if email is None or token_type != "reset_password":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid reset password token",
                )

            return email

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid reset password token",
            )


auth_service = Auth()

