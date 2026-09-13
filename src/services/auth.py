from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from os import getenv

import pickle
import redis
import bcrypt

from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import settings

load_dotenv()

class Auth:

    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')

        return bcrypt.checkpw(
            password_bytes,
            hashed_password_bytes
        )

    @staticmethod
    def get_password_hash(password: str):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")



    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update(
            {
                'iat': datetime.utcnow(),
                'exp': expire,
                'scope': 'access_token'
            }
        )

        encode_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encode_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days = 7)

        to_encode.update(
            {
                'iat' : datetime.utcnow(),
                'exp' : expire,
                'scope' : 'refresh_token'
            }
        )
        encode_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encode_refresh_token

    async def decode_refresh_token(self, refresh_token: str):

        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid scope for token'
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not valide credentials"
            )


    async def get_current_user(
            self, 
            token: str = Depends(oauth2_scheme), 
            db: Session = Depends(get_db)
            ):

        credentials_exeption = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials",
            headers={'WWW-Authenticate' : 'Bearer'},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload['sub']
                if email is None:
                    raise credentials_exeption
            else:
                raise credentials_exeption
        except JWTError as e:
            raise credentials_exeption

        user = self.r.get(f"user:{email}")

        if user is None:
            user = await repository_users.get_user_by_email(email,db)
            if user is None:
                raise credentials_exeption
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user

    async def create_email_token(self, data: dict):

        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {
                'iat' : datetime.utcnow(),
                'exp' : expire
            }
        )

        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload['sub']
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid token for email"
            )

    async def create_reset_password_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update(
            {
                'iat' : datetime.utcnow(),
                'exp' : expire,
                'type' : 'reset_password'
            }
        )

        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def decode_reset_password_token(self, token: str):
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )

            email = payload.get('sub')
            token_type = payload.get('type')

            if email is None or token_type != 'reset_password':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid reset password token"
                )
            return email

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid reset password token"
            )
        
auth_service = Auth()

