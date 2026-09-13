from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from dotenv import load_dotenv
import os

from src.services.auth import auth_service
from src.conf.config import settings

load_dotenv()


conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):

    try:
        token_verification = await auth_service.create_email_token({"sub" : email})
        message = MessageSchema(
            subject='Confirm your email',
            recipients=[email],
            template_body={
                "host" : host, 
                'username' : username, 
                'token' : token_verification
            },
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name='email_template.html')

    except ConnectionErrors as err:
        print(err)

async def send_reset_password_email(email: EmailStr, username: str, host: str):

    try:
        print("START EMAIL:", email)
        reset_token = await auth_service.create_reset_password_token({"sub": email})

        print("TOKEN CREATED")
        message = MessageSchema(
            subject="Account security",
            recipients=[email],
            template_body={
                'host' : host,
                'username' : username,
                'token' : reset_token
            },
            subtype=MessageType.html
            )

        fm = FastMail(conf)
        await fm.send_message(message, template_name='password_reset_email.html')

        print("EMAIL SENT:", email)
    except ConnectionErrors as err:
        print(err)

