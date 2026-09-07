from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, UserLogin
from src.repository import users as user_repository
from src.services.auth import auth_service

router = APIRouter(prefix='/auth', tags=['auth'])
security = HTTPBearer()

@router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, db: Session = Depends(get_db)):

    exist_user = await user_repository.get_user_by_email(body.email,db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Account already exists"
        )

    body.password = auth_service.get_password_hash(body.password)
    new_user = await user_repository.create_user(body, db)

    return {
        'user' : new_user,
        'detail' : "User successfully created"
    }

@router.post('/login', response_model=TokenModel)
async def login(
    body: UserLogin, 
    db: Session = Depends(get_db)):
    user = await user_repository.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Invalid email'
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Invalid password'
        )

    access_token = await auth_service.create_access_token(data={'sub' : user.email})
    refresh_token = await auth_service.create_refresh_token(data={'sub' : user.email})

    await user_repository.update_token(user, refresh_token, db)

    return {
        'access_token' : access_token,
        'refresh_token' : refresh_token,
        'token_type' : 'bearer'
    }

@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)):

    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await user_repository.get_user_by_email(email, db)

    if user is None:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token'
    )
    if user.refresh_token != token:
        await user_repository.update_token(user, None, db)
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED, 
             detail='Invalid refresh token'
        )

    access_token = await auth_service.create_access_token(data = {'sub' : email})
    refresh_token = await auth_service.create_refresh_token(data={'sub' : email})

    await user_repository.update_token(user, refresh_token, db)
    return {
        'access_token' : access_token,
        'refresh_token' : refresh_token,
        'token_type' : 'bearer'
    }



