from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request, File, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import cloudinary 
import cloudinary.uploader 

import pathlib

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, UserLogin, RequestEmail, UserDb
from src.repository import users as user_repository
from src.services.auth import auth_service
from src.services.email import send_email
from src.database.models import User
from src.conf.config import settings 

router = APIRouter(prefix='/users', tags=['users'])
security = HTTPBearer()


@router.get('/me/', response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user

@router.patch("/avatar", response_model=UserDb)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)):

    cloudinary.config(
        cloud_name = settings.cloudinary_name,
        api_key = settings.cloudinary_api_key,
        api_secret = settings.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(
        file.file,
        public_id = f"ContactsApp/{current_user.username}",
        overwrite = True
    )

    src_url = cloudinary.CloudinaryImage(
        f"ContactsApp/{current_user.username}"
    ).build_url(
        width=250, 
        height=250,
        crop="fill",
        version=r.get('version')
    )

    user = await user_repository.update_avatar(current_user.email, src_url, db)

    return user

