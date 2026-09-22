import bcrypt
import pickle
import pytest

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from jose import jwt

import src.services.auth as auth_module

from src.services.auth import auth_service
from src.services.auth import Auth


@pytest.mark.parametrize(
    "password, expected",
    [
        ("123456789", True),
        ("wrong_password", False),
        ("",False), 
    ]
)

def test_verify_password(password, expected):

    original_password = "123456789"
    hashed_password = bcrypt.hashpw(
        original_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    result = Auth.verify_password(
        password,
        hashed_password,
    )

    assert result is expected

def test_get_password_hash():
    password = "123456789"
    hashed_password = Auth.get_password_hash(password)

    assert Auth.verify_password(
        password,
        hashed_password,
    ) is True

def test_get_password_hash_generate_different_hashes():
    password = "123456789"

    first_hash = Auth.get_password_hash(password)
    second_hash = Auth.get_password_hash(password)

    assert first_hash != second_hash


def test_get_password_hash_generate_valid_hashs():

    password = "123456789"
    
    first_hash = Auth.get_password_hash(password)
    second_hash = Auth.get_password_hash(password)

    assert Auth.verify_password(password, first_hash) is True
    assert Auth.verify_password(password, second_hash) is True



@pytest.mark.asyncio
async def test_create_access_token():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_access_token(data)

    assert isinstance(token, str)
    assert token


@pytest.mark.asyncio
async def test_create_access_token_payload():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_access_token(data)

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    assert payload["sub"] == "user@example.com"
    assert payload["scope"] == "access_token"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload


@pytest.mark.asyncio
async def test_create_access_token_custom_expiration():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_access_token(
        data,
        expires_delta=60,
    )

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    assert 59 <= payload["exp"] - payload["iat"] <= 60


@pytest.mark.asyncio
async def test_create_access_token_default_expiration():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_access_token(data)

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    assert 899 <= payload["exp"] - payload["iat"] <= 900


@pytest.mark.asyncio
async def test_create_access_token_does_not_modify_data():
    data = {"sub": "user@example.com"}
    original_data = data.copy()

    await auth_service.create_access_token(data)

    assert data == original_data


@pytest.mark.asyncio
async def test_create_refresh_token():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_refresh_token(data)

    assert isinstance(token, str)
    assert token


@pytest.mark.asyncio
async def test_create_refresh_token_payload():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_refresh_token(data)

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    assert payload["sub"] == "user@example.com"
    assert payload["scope"] == "refresh_token"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload


@pytest.mark.asyncio
async def test_create_refresh_token_custom_expiration():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_refresh_token(
        data,
        expires_delta=60,
    )

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    assert 59 <= payload["exp"] - payload["iat"] <= 60


@pytest.mark.asyncio
async def test_create_refresh_token_default_expiration():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_refresh_token(data)

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    expected_lifetime = 7 * 24 * 60 * 60

    assert (
        expected_lifetime - 1
        <= payload["exp"] - payload["iat"]
        <= expected_lifetime
    )


@pytest.mark.asyncio
async def test_decode_refresh_token():
    email = "user@example.com"

    token = await auth_service.create_refresh_token(
        {"sub": email}
    )

    result = await auth_service.decode_refresh_token(token)

    assert result == email


@pytest.mark.asyncio
async def test_decode_refresh_token_invalid_scope():
    token = await auth_service.create_access_token(
        {"sub": "user@example.com"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.decode_refresh_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid scope for token"


@pytest.mark.asyncio
async def test_decode_refresh_token_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.decode_refresh_token("invalid_token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not valide credentials"


@pytest.mark.asyncio
async def test_create_email_token():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_email_token(data)

    assert isinstance(token, str)
    assert token


@pytest.mark.asyncio
async def test_create_email_token_payload():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_email_token(data)

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    assert payload["sub"] == "user@example.com"
    assert "iat" in payload
    assert "exp" in payload

    expected_lifetime = 7 * 24 * 60 * 60

    assert (
        expected_lifetime - 1
        <= payload["exp"] - payload["iat"]
        <= expected_lifetime
    )


@pytest.mark.asyncio
async def test_get_email_from_token():
    email = "user@example.com"

    token = await auth_service.create_email_token(
        {"sub": email}
    )

    result = await auth_service.get_email_from_token(token)

    assert result == email


@pytest.mark.asyncio
async def test_get_email_from_token_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_email_from_token("invalid_token")

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Invalid token for email"


@pytest.mark.asyncio
async def test_create_reset_password_token():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_reset_password_token(data)

    assert isinstance(token, str)
    assert token


@pytest.mark.asyncio
async def test_create_reset_password_token_payload():
    data = {"sub": "user@example.com"}

    token = await auth_service.create_reset_password_token(data)

    payload = jwt.decode(
        token,
        auth_service.SECRET_KEY,
        algorithms=[auth_service.ALGORITHM],
    )

    assert payload["sub"] == "user@example.com"
    assert payload["type"] == "reset_password"
    assert "iat" in payload
    assert "exp" in payload

    expected_lifetime = 15 * 60

    assert (
        expected_lifetime - 1
        <= payload["exp"] - payload["iat"]
        <= expected_lifetime
    )


@pytest.mark.asyncio
async def test_decode_reset_password_token():
    email = "user@example.com"

    token = await auth_service.create_reset_password_token(
        {"sub": email}
    )

    result = await auth_service.decode_reset_password_token(token)

    assert result == email


@pytest.mark.asyncio
async def test_decode_reset_password_token_invalid_type():
    token = await auth_service.create_email_token(
        {"sub": "user@example.com"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.decode_reset_password_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid reset password token"


@pytest.mark.asyncio
async def test_decode_reset_password_token_without_email():
    token = await auth_service.create_reset_password_token(
        {"email": "user@example.com"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.decode_reset_password_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid reset password token"


@pytest.mark.asyncio
async def test_decode_reset_password_token_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.decode_reset_password_token("invalid_token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid reset password token"


@pytest.mark.asyncio
async def test_get_current_user_from_redis(monkeypatch):
    """
    Tests retrieving a user from Redis cache.
    The database must not be called when the user is found in Redis.
    """

    email = "user@example.com"

    token = await auth_service.create_access_token(
        {"sub": email}
    )

    cached_user = {
        "id": 1,
        "email": email,
        "username": "testuser",
    }

    mock_redis = MagicMock()

    mock_redis.get.return_value = pickle.dumps(cached_user)

    monkeypatch.setattr(
        auth_service,
        "r",
        mock_redis,
    )

    mock_repository = AsyncMock()

    monkeypatch.setattr(
        auth_module.repository_users,
        "get_user_by_email",
        mock_repository,
    )

    db = MagicMock()

    result = await auth_service.get_current_user(
        token,
        db,
    )

    assert result == cached_user

    mock_redis.get.assert_called_once_with(
        f"user:{email}"
    )

    mock_repository.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_from_database(monkeypatch):
    """
    Tests retrieving a user from the database when
    the user is not found in Redis.
    """

    email = "user@example.com"

    token = await auth_service.create_access_token(
        {"sub": email}
    )

    user_from_database = SimpleNamespace(
        id=1,
        email=email,
        username="testuser",
    )

    mock_redis = MagicMock()

    mock_redis.get.return_value = None

    monkeypatch.setattr(
        auth_service,
        "r",
        mock_redis,
    )

    mock_repository = AsyncMock(
        return_value=user_from_database
    )

    monkeypatch.setattr(
        auth_module.repository_users,
        "get_user_by_email",
        mock_repository,
    )

    db = MagicMock()

    result = await auth_service.get_current_user(
        token,
        db,
    )

    assert result is user_from_database

    mock_redis.get.assert_called_once_with(
        f"user:{email}"
    )

    mock_repository.assert_awaited_once_with(
        email,
        db,
    )

    mock_redis.set.assert_called_once()

    cache_key, cache_value = (
        mock_redis.set.call_args.args
    )

    assert cache_key == f"user:{email}"

    cached_user = pickle.loads(cache_value)

    assert cached_user is not None

    mock_redis.expire.assert_called_once_with(
        f"user:{email}",
        900,
    )


@pytest.mark.asyncio
async def test_get_current_user_user_not_found_in_database(
    monkeypatch,
):
    """
    Tests the case when the user is not found
    in Redis and in the database.
    """

    email = "user@example.com"

    token = await auth_service.create_access_token(
        {"sub": email}
    )

    mock_redis = MagicMock()

    mock_redis.get.return_value = None

    monkeypatch.setattr(
        auth_service,
        "r",
        mock_redis,
    )

    mock_repository = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        auth_module.repository_users,
        "get_user_by_email",
        mock_repository,
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_current_user(
            token,
            db,
        )

    assert exc_info.value.status_code == 401

    mock_repository.assert_awaited_once_with(
        email,
        db,
    )

    mock_redis.set.assert_not_called()

    mock_redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_invalid_jwt():
    """
    Tests the case when an invalid JWT is provided.
    """

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_current_user(
            "invalid_token",
            db,
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_scope(monkeypatch):
    """
    Tests the case when a refresh token is provided
    instead of an access token.
    """

    email = "user@example.com"

    token = await auth_service.create_refresh_token(
        {"sub": email}
    )

    mock_redis = MagicMock()

    monkeypatch.setattr(
        auth_service,
        "r",
        mock_redis,
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_current_user(
            token,
            db,
        )

    assert exc_info.value.status_code == 401

    mock_redis.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_missing_sub(monkeypatch):
    """
    Tests the case when the JWT does not contain
    the sub claim.
    """

    token = await auth_service.create_access_token({})

    mock_redis = MagicMock()

    monkeypatch.setattr(
        auth_service,
        "r",
        mock_redis,
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_current_user(
            token,
            db,
        )

    assert exc_info.value.status_code == 401

    mock_redis.get.assert_not_called()