
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi_mail.errors import ConnectionErrors

from src.services.email import (
    send_email,
    send_reset_password_email,
)


@pytest.mark.asyncio
async def test_send_email(monkeypatch):
    mock_token = "verification-token"

    mock_create_token = AsyncMock(return_value=mock_token)
    monkeypatch.setattr(
        "src.services.email.auth_service.create_email_token",
        mock_create_token,
    )

    mock_send_message = AsyncMock()

    mock_fast_mail = MagicMock()
    mock_fast_mail.send_message = mock_send_message

    monkeypatch.setattr(
        "src.services.email.FastMail",
        MagicMock(return_value=mock_fast_mail),
    )

    await send_email(
        email="test@example.com",
        username="testuser",
        host="http://localhost:8000",
    )

    mock_create_token.assert_awaited_once_with(
        {"sub": "test@example.com"}
    )

    mock_send_message.assert_awaited_once()

    message = mock_send_message.call_args.args[0]

    assert message.subject == "Confirm your email"
    assert message.recipients[0].email == "test@example.com"
    assert message.template_body["host"] == "http://localhost:8000"
    assert message.template_body["username"] == "testuser"
    assert message.template_body["token"] == mock_token

@pytest.mark.asyncio
async def test_send_reset_password_email(monkeypatch):
    mock_token = "reset-token"

    mock_create_token = AsyncMock(return_value=mock_token)
    monkeypatch.setattr(
        "src.services.email.auth_service.create_reset_password_token",
        mock_create_token,
    )

    mock_send_message = AsyncMock()

    mock_fast_mail = MagicMock()
    mock_fast_mail.send_message = mock_send_message

    monkeypatch.setattr(
        "src.services.email.FastMail",
        MagicMock(return_value=mock_fast_mail),
    )

    await send_reset_password_email(
        email="test@example.com",
        username="testuser",
        host="http://localhost:8000",
    )

    mock_create_token.assert_awaited_once_with(
        {"sub": "test@example.com"}
    )

    mock_send_message.assert_awaited_once()

    message = mock_send_message.call_args.args[0]

    assert message.subject == "Account security"
    assert message.recipients[0].email == "test@example.com"
    assert message.template_body["host"] == "http://localhost:8000"
    assert message.template_body["username"] == "testuser"
    assert message.template_body["token"] == mock_token



@pytest.mark.asyncio
async def test_send_email_connection_error(monkeypatch, capsys):
    mock_create_token = AsyncMock(return_value="verification-token")
    monkeypatch.setattr(
        "src.services.email.auth_service.create_email_token",
        mock_create_token,
    )

    mock_send_message = AsyncMock(
        side_effect=ConnectionErrors("SMTP connection error")
    )

    mock_fast_mail = MagicMock()
    mock_fast_mail.send_message = mock_send_message

    monkeypatch.setattr(
        "src.services.email.FastMail",
        MagicMock(return_value=mock_fast_mail),
    )

    await send_email(
        email="test@example.com",
        username="testuser",
        host="http://localhost:8000",
    )

    captured = capsys.readouterr()

    assert "SMTP connection error" in captured.out


@pytest.mark.asyncio
async def test_send_reset_password_email_connection_error(
    monkeypatch,
    capsys,
):
    mock_create_token = AsyncMock(return_value="reset-token")
    monkeypatch.setattr(
        "src.services.email.auth_service.create_reset_password_token",
        mock_create_token,
    )

    mock_send_message = AsyncMock(
        side_effect=ConnectionErrors("SMTP connection error")
    )

    mock_fast_mail = MagicMock()
    mock_fast_mail.send_message = mock_send_message

    monkeypatch.setattr(
        "src.services.email.FastMail",
        MagicMock(return_value=mock_fast_mail),
    )

    await send_reset_password_email(
        email="test@example.com",
        username="testuser",
        host="http://localhost:8000",
    )

    captured = capsys.readouterr()

    assert "SMTP connection error" in captured.out

