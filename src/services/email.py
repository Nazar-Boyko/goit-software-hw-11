from pathlib import Path

from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig,
    MessageType,
)
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service
from src.conf.config import settings


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
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(
    email: EmailStr,
    username: str,
    host: str,
):
    """
    Sends an email confirmation message to a user.

    Creates an email verification token, prepares an HTML email
    using the configured template, and sends the message through
    the FastMail SMTP service.

    :param email: The email address of the user who should receive
        the confirmation message.
    :type email: EmailStr
    :param username: The username of the user who should receive
        the confirmation message.
    :type username: str
    :param host: The base URL of the application used to create
        the email confirmation link.
    :type host: str
    :return: None
    :rtype: None
    :raises ConnectionErrors: If a connection error occurs while
        sending the email.
    """

    try:
        token_verification = await auth_service.create_email_token(
            {"sub": email}
        )

        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)

        await fm.send_message(
            message,
            template_name="email_template.html",
        )

    except ConnectionErrors as err:
        print(err)


async def send_reset_password_email(
    email: EmailStr,
    username: str,
    host: str,
):
    """
    Sends a password reset email to a user.

    Creates a password reset token, prepares an HTML email
    using the password reset template, and sends the message
    through the configured FastMail SMTP service.

    :param email: The email address of the user who requested
        a password reset.
    :type email: EmailStr
    :param username: The username of the user who requested
        a password reset.
    :type username: str
    :param host: The base URL of the application used to create
        the password reset link.
    :type host: str
    :return: None
    :rtype: None
    :raises ConnectionErrors: If a connection error occurs while
        sending the email.
    """

    try:
        print("START EMAIL:", email)

        reset_token = await auth_service.create_reset_password_token(
            {"sub": email}
        )

        print("TOKEN CREATED")

        message = MessageSchema(
            subject="Account security",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": reset_token,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)

        await fm.send_message(
            message,
            template_name="password_reset_email.html",
        )

        print("EMAIL SENT:", email)

    except ConnectionErrors as err:
        print(err)
