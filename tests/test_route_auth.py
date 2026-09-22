from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException

from src.database.models import User


def test_create_user(client, user, monkeypatch):

    mock_send_email = MagicMock()
    monkeypatch.setattr('src.routes.auth.send_email', mock_send_email)

    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]

def test_repeat_create_user(client, user):
    response = client.post(
        "/api/auth/signup",
        json=user,
    )

    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"

def test_login_user_not_confirmed(client, user):
    response = client.post(
        "/api/auth/login",
        data={
            "username" : user.get("email"),
            "password" : user.get("password")
        },
    )  
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"

def test_login_user(client, session, user):

    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={
            "username" : user.get("email"),
            "password" : user.get("password")
        },
    )  
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, user):

    response = client.post(
        "/api/auth/login",
        data = {
            "username" : user.get("email"),
            "password" : "password",
        }
    )

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"

def test_login_wrong_email(client, user):
    response = client.post(
        "/api/auth/login",
        data={
            "username" : "username",
            "password" : user.get("password")
            }
        )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


def test_refresh_token(client, session, user):
    
    current_user: User = session.query(User).filter(
        User.email == user.get("email")
    ).first()

    current_user.confirmed = True
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={
            "username": user.get("email"),
            "password": user.get("password"),
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()
    refresh_token = data["refresh_token"]

    response = client.get(
        "/api/auth/refresh_token",
        headers={
            "Authorization": f"Bearer {refresh_token}"
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] != refresh_token

def test_refresh_token_invalid(client):

    response = client.get(
        "/api/auth/refresh_token",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401, response.text


def test_refresh_token_user_not_found(client, monkeypatch):

    mock_decode = AsyncMock(
        return_value = "unknown@example.com"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.decode_refresh_token",
        mock_decode,
    )

    mock_get_user = AsyncMock(return_value = None)

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user
    )

    response = client.get(
        '/api/auth/refresh_token',
        headers={
            "Authorization": "Bearer valid_refresh_token"
        }
    )

    assert response.status_code == 401, response.text


    data = response.json()

    assert data["detail"] == "Invalid refresh token"

def test_refresh_token_not_match(client, monkeypatch):

    current_user = MagicMock()
    current_user.refresh_token = "another_refresh_token"

    mock_decode = AsyncMock(
        return_value="deadpool@example.com"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.decode_refresh_token",
        mock_decode,
    )

    mock_get_user = AsyncMock(
        return_value=current_user
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    mock_update_token = AsyncMock()

    monkeypatch.setattr(
        "src.routes.auth.user_repository.update_token",
        mock_update_token,
    )

    response = client.get(
        "/api/auth/refresh_token",
        headers={
            "Authorization": "Bearer old_refresh_token"
        },
    )

    assert response.status_code == 401, response.text

    data = response.json()

    assert data["detail"] == "Invalid refresh token"

def test_confirmed_email_success(client, monkeypatch):

    current_user = MagicMock()
    current_user.confirmed = False

    mock_get_email = AsyncMock(
        return_value="test@test.com"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.get_email_from_token",
        mock_get_email
    )

    mock_get_user = AsyncMock(
        return_value=current_user
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user
    )

    mock_confirmed_email = AsyncMock()

    monkeypatch.setattr(
        "src.routes.auth.user_repository.confirmed_email",
        mock_confirmed_email
    )

    response = client.get(
        "/api/auth/confirmed_email/test_token"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Email confirmed"

    mock_get_email.assert_awaited_once_with(
        "test_token"
    )

    mock_get_user.assert_awaited_once()

    mock_confirmed_email.assert_awaited_once()

def test_confirmed_email_user_not_found(client, monkeypatch):
    mock_get_email = AsyncMock(
            return_value="unknown@test.com"
        )
    
    monkeypatch.setattr(
        "src.routes.auth.auth_service.get_email_from_token",
        mock_get_email
    )

    mock_get_user = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user
    )

    mock_confirmed_email = AsyncMock()

    monkeypatch.setattr(
        "src.routes.auth.user_repository.confirmed_email",
        mock_confirmed_email
    )

    response = client.get(
        "/api/auth/confirmed_email/test_token"
    )

    assert response.status_code == 400, response.text

    data = response.json()

    assert data["detail"] == "Verification error"

    mock_get_email.assert_awaited_once_with("test_token")

    mock_get_user.assert_awaited_once()

    mock_confirmed_email.assert_not_awaited()

def test_confirmed_email_already_confirmed(client, monkeypatch):

    current_user = MagicMock()
    current_user.confirmed = True

    mock_get_email = AsyncMock(
        return_value="test@test.com"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.get_email_from_token",
        mock_get_email,
    )

    mock_get_user = AsyncMock(
        return_value=current_user
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    mock_confirmed_email = AsyncMock()

    monkeypatch.setattr(
        "src.routes.auth.user_repository.confirmed_email",
        mock_confirmed_email,
    )

    response = client.get(
        "/api/auth/confirmed_email/test_token"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Your email is already confirmed"

    mock_get_email.assert_awaited_once_with("test_token")
    mock_get_user.assert_awaited_once()

    mock_confirmed_email.assert_not_awaited()


def test_confirmed_email_token_wrong(client, monkeypatch):
    mock_get_email = AsyncMock(
        side_effect=HTTPException(
            status_code=400,
            detail='Invalid token'
        ),
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.get_email_from_token",
        mock_get_email,
    )

    response = client.get(
        "/api/auth/confirmed_email/invalid_token"
    )

    assert response.status_code == 400, response.text

    data = response.json()

    assert data["detail"] == "Invalid token"

    mock_get_email.assert_awaited_once_with("invalid_token")

    
# -------------------------
# request_email
# -------------------------

def test_request_email_user_not_found(client, monkeypatch):
    mock_get_user = AsyncMock(return_value=None)

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    response = client.post(
        "/api/auth/request_email",
        json={"email": "unknown@test.com"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data == {}

    mock_get_user.assert_awaited_once()


def test_request_email_already_confirmed(client, monkeypatch):
    current_user = MagicMock()
    current_user.confirmed = True
    current_user.email = "test@test.com"
    current_user.username = "test"

    mock_get_user = AsyncMock(
        return_value=current_user
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    mock_send_email = AsyncMock()

    monkeypatch.setattr(
        "src.routes.auth.send_email",
        mock_send_email,
    )

    response = client.post(
        "/api/auth/request_email",
        json={"email": "test@test.com"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Your email is already confirmed"

    mock_get_user.assert_awaited_once()
    mock_send_email.assert_not_awaited()


def test_request_email_user_not_confirmed(client, monkeypatch):
    current_user = MagicMock()
    current_user.confirmed = False
    current_user.email = "test@test.com"
    current_user.username = "test"

    mock_get_user = AsyncMock(
        return_value=current_user
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    mock_send_email = AsyncMock()

    monkeypatch.setattr(
        "src.routes.auth.send_email",
        mock_send_email,
    )

    response = client.post(
        "/api/auth/request_email",
        json={"email": "test@test.com"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Check your email for confirmation."

    mock_get_user.assert_awaited_once()
    mock_send_email.assert_awaited_once()


# -------------------------
# reset_password
# -------------------------

def test_reset_password_user_not_found(client, monkeypatch):
    mock_get_user = AsyncMock(return_value=None)

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    response = client.post(
        "/api/auth/reset_password",
        json={"email": "unknown@test.com"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == (
        "A user with this email does not exist, please register."
    )

    mock_get_user.assert_awaited_once()


def test_reset_password_user_found(client, monkeypatch):
    current_user = MagicMock()
    current_user.email = "test@test.com"
    current_user.username = "test"

    mock_get_user = AsyncMock(
        return_value=current_user
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    mock_send_email = AsyncMock()

    monkeypatch.setattr(
        "src.routes.auth.send_reset_password_email",
        mock_send_email,
    )

    response = client.post(
        "/api/auth/reset_password",
        json={"email": "test@test.com"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Check your email to reset your password"

    mock_get_user.assert_awaited_once()
    mock_send_email.assert_awaited_once()


# -------------------------
# reset_password_form
# -------------------------

def test_reset_password_form_success(client, monkeypatch):
    mock_decode = AsyncMock(
        return_value="test@test.com"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.decode_reset_password_token",
        mock_decode,
    )

    token = "valid_token"

    response = client.get(
        f"/api/auth/reset_password/{token}"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Enter your new password"
    assert data["email"] == "test@test.com"
    assert data["token"] == token

    mock_decode.assert_awaited_once_with(token)


def test_reset_password_form_invalid_token(client, monkeypatch):
    mock_decode = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.decode_reset_password_token",
        mock_decode,
    )

    token = "invalid_token"

    response = client.get(
        f"/api/auth/reset_password/{token}"
    )

    assert response.status_code == 400, response.text

    data = response.json()

    assert data["detail"] == "Invalid or expired token"

    mock_decode.assert_awaited_once_with(token)


# -------------------------
# reset_password_confirm
# -------------------------

def test_reset_password_confirm_success(client, monkeypatch):
    current_user = MagicMock()
    current_user.email = "test@test.com"
    current_user.password = "old_password"

    mock_decode = AsyncMock(
        return_value="test@test.com"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.decode_reset_password_token",
        mock_decode,
    )

    mock_get_user = AsyncMock(
        return_value=current_user
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    mock_hash = MagicMock(
        return_value="hashed_new_password"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.get_password_hash",
        mock_hash,
    )

    response = client.post(
        "/api/auth/reset_password/confirm/valid_token",
        json={"password": "new_password"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Password successfully reset"
    assert current_user.password == "hashed_new_password"

    mock_decode.assert_awaited_once_with("valid_token")
    mock_get_user.assert_awaited_once()
    mock_hash.assert_called_once_with("new_password")


def test_reset_password_confirm_user_not_found(client, monkeypatch):
    mock_decode = AsyncMock(
        return_value="unknown@test.com"
    )

    monkeypatch.setattr(
        "src.routes.auth.auth_service.decode_reset_password_token",
        mock_decode,
    )

    mock_get_user = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        "src.routes.auth.user_repository.get_user_by_email",
        mock_get_user,
    )

    response = client.post(
        "/api/auth/reset_password/confirm/valid_token",
        json={"password": "new_password"},
    )

    assert response.status_code == 404, response.text

    data = response.json()

    assert data["detail"] == "User not found"

    mock_decode.assert_awaited_once_with("valid_token")
    mock_get_user.assert_awaited_once()

