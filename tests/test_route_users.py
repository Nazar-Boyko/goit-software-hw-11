from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException



def test_read_users_me(authorized_client, current_user):

    response = authorized_client.get("/api/users/me")

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == current_user.id
    assert data["username"] == current_user.username
    assert data["email"] == current_user.email
    assert data["confirmed"] == current_user.confirmed
    assert data["avatar"] == current_user.avatar
    

def test_change_avatar_user(authorized_client, monkeypatch, current_user):


    updated_user = {
        "id": 1,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": "2026-09-21T12:00:00",
        "confirmed": True,
        "avatar": "https://cloudinary.com/avatar.jpg"
    }

    mock_upload = MagicMock(
        return_value= {"version": 123456}
    )

    mock_build_url = MagicMock(
        return_value=updated_user["avatar"]
    )

    mock_update_avatar = AsyncMock(
        return_value = updated_user
    )

    monkeypatch.setattr(
        "src.routes.users.cloudinary.uploader.upload",
        mock_upload,
    )

    monkeypatch.setattr(
        "src.routes.users.cloudinary.CloudinaryImage",
        lambda public_id: SimpleNamespace(
            build_url=mock_build_url
            ),
        )

    monkeypatch.setattr(
        "src.routes.users.user_repository.update_avatar",
        mock_update_avatar,
    )

    response = authorized_client.patch(
        "/api/users/avatar",
        files={
            'file': (
                "avatar.jpg",
                b"fake image content",
                "image/jpeg"
                )
            }
        )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["email"] == updated_user["email"]
    assert data["avatar"] == updated_user["avatar"]

    mock_upload.assert_called_once()
    mock_update_avatar.assert_called_once()


