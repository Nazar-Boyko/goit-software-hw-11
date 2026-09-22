from unittest.mock import AsyncMock

from src.database.models import Contact, User


# =========================
# GET /contacts/
# =========================

def test_get_contacts(
    authorized_client,
    monkeypatch,
    contact,
    current_user,
):
    mock_get_contacts = AsyncMock(
        return_value=[contact]
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.get_contacts",
        mock_get_contacts,
    )

    response = authorized_client.get(
        "/api/contacts/",
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == contact.id

    mock_get_contacts.assert_awaited_once_with(
        0,
        100,
        current_user,
        mock_get_contacts.await_args.args[3],
    )


# =========================
# GET /contacts/search
# =========================

def test_search_contacts(
    authorized_client,
    monkeypatch,
    contact,
    current_user,
):
    mock_search_contacts = AsyncMock(
        return_value=[contact]
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.search_contacts",
        mock_search_contacts,
    )

    response = authorized_client.get(
        "/api/contacts/search",
        params={
            "first_name": "Nazar",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == contact.id

    args = mock_search_contacts.await_args.args

    assert args[0] == "Nazar"
    assert args[1] is None
    assert args[2] is None
    assert args[3] == current_user


# =========================
# GET /contacts/upcoming_birthday
# =========================

def test_get_upcoming_birthday(
    authorized_client,
    monkeypatch,
    contact,
    current_user,
):
    mock_get_upcoming = AsyncMock(
        return_value=[contact]
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.get_upcoming_birthdays",
        mock_get_upcoming,
    )

    response = authorized_client.get(
        "/api/contacts/upcoming_birthday",
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == contact.id

    args = mock_get_upcoming.await_args.args

    assert args[0] == 0
    assert args[1] == 100
    assert args[2] == current_user


# =========================
# GET /contacts/{contact_id}
# =========================

def test_read_contact(
    authorized_client,
    monkeypatch,
    contact,
    current_user,
):
    mock_get_contact = AsyncMock(
        return_value=contact
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.get_contact",
        mock_get_contact,
    )

    response = authorized_client.get(
        f"/api/contacts/{contact.id}",
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == contact.id

    args = mock_get_contact.await_args.args

    assert args[0] == contact.id
    assert args[1] == current_user


def test_read_contact_not_found(
    authorized_client,
    monkeypatch,
    current_user,
):
    mock_get_contact = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.get_contact",
        mock_get_contact,
    )

    response = authorized_client.get(
        "/api/contacts/999",
    )

    assert response.status_code == 404, response.text

    data = response.json()

    assert data["detail"] == "Contact not found"

    args = mock_get_contact.await_args.args

    assert args[0] == 999
    assert args[1] == current_user


# =========================
# POST /contacts/
# =========================

def test_create_contact(
    authorized_client,
    monkeypatch,
    contact,
    current_user,
):
    mock_create_contact = AsyncMock(
        return_value=contact
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.create_contact",
        mock_create_contact,
    )

    contact_data = {
        "first_name": "Nazar",
        "last_name": "Boyko",
        "email": "nazar@test.com",
        "phone": "+380991234567",
        "birthday": "2000-05-10",
        "additional_information": "Test contact",
    }

    response = authorized_client.post(
        "/api/contacts/",
        json=contact_data,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["id"] == contact.id

    args = mock_create_contact.await_args.args

    assert args[0].first_name == contact_data["first_name"]
    assert args[0].last_name == contact_data["last_name"]
    assert args[1] == current_user


# =========================
# PUT /contacts/{contact_id}
# =========================

def test_update_contact(
    authorized_client,
    monkeypatch,
    contact,
    current_user,
):
    mock_update_contact = AsyncMock(
        return_value=contact
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.update_contact",
        mock_update_contact,
    )

    contact_data = {
        "first_name": "Updated",
        "last_name": "Boyko",
        "email": "updated@test.com",
        "phone": "+380991234567",
        "birthday": "2000-05-10",
        "additional_information": "Updated contact",
    }

    response = authorized_client.put(
        f"/api/contacts/{contact.id}",
        json=contact_data,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == contact.id

    args = mock_update_contact.await_args.args

    assert args[0] == contact.id
    assert args[1].first_name == contact_data["first_name"]
    assert args[2] == current_user


def test_update_contact_not_found(
    authorized_client,
    monkeypatch,
    current_user,
):
    mock_update_contact = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.update_contact",
        mock_update_contact,
    )

    contact_data = {
        "first_name": "Updated",
        "last_name": "Boyko",
        "email": "updated@test.com",
        "phone": "+380991234567",
        "birthday": "2000-05-10",
        "additional_information": "Updated contact",
    }

    response = authorized_client.put(
        "/api/contacts/999",
        json=contact_data,
    )

    assert response.status_code == 404, response.text

    data = response.json()

    assert data["detail"] == "Contact not found"

    args = mock_update_contact.await_args.args

    assert args[0] == 999
    assert args[1].first_name == contact_data["first_name"]
    assert args[2] == current_user


# =========================
# DELETE /contacts/{contact_id}
# =========================

def test_remove_contact(
    authorized_client,
    monkeypatch,
    contact,
    current_user,
):
    mock_remove_contact = AsyncMock(
        return_value=contact
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.remove_contact",
        mock_remove_contact,
    )

    response = authorized_client.delete(
        f"/api/contacts/{contact.id}",
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == contact.id

    args = mock_remove_contact.await_args.args

    assert args[0] == contact.id
    assert args[1] == current_user


def test_remove_contact_not_found(
    authorized_client,
    monkeypatch,
    current_user,
):
    mock_remove_contact = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        "src.routes.contacts.contacts_repository.remove_contact",
        mock_remove_contact,
    )

    response = authorized_client.delete(
        "/api/contacts/999",
    )

    assert response.status_code == 404, response.text

    data = response.json()

    assert data["detail"] == "Contact not found"

    args = mock_remove_contact.await_args.args

    assert args[0] == 999
    assert args[1] == current_user