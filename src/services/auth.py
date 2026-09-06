from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import bcrypt


from src.database.db import get_db
from src.repository import users as repository_users


class Auth:

    SECRET_KEY = 'secret_key'
    ALGORITHM = 'HS256'
    oauth2_sheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

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

    async def create_refrash_token(self, data: dict, expireles_delta: Optional[float] = None):
        to_encode = data.copy()
        if expireles_delta:
            expire = datetime.utcnow() + timedelta(seconds=expireles_delta)
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
            token: str = Depends(oauth2_sheme), 
            db: Session = Depends(get_db)
            ):

        credentials_exeption = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials",
            headers={'WWW-Authenticate' : 'Bearer'},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'aceess_token':
                email = payload['sub']
                if email is None:
                    raise credentials_exeption
            else:
                raise credentials_exeption
        except JWTError as e:
            credentials_exeption

        user = await repository_users.get_user_by_email(email,db)

        if user is None:
            raise credentials_exeption
        return user

auth_service = Auth()

