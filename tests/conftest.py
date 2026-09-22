import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from main import app
from src.database.db import get_db
from src.database.models import Base, Contact, User
from src.services.auth import auth_service
from src.routes.contacts import contacts_rate_limiter

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def session():

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db=TestingSessionLocal()
    try: 
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def mock_fastapi_lmiter():
    app.dependency_overrides[contacts_rate_limiter] = mock_rate_limiter

    yield

    app.dependency_overrides.pop(contacts_rate_limiter, None)

async def mock_rate_limiter():
    pass

@pytest.fixture(scope="module")
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

@pytest.fixture
def authorized_client(client, current_user):
    app.dependency_overrides[
        auth_service.get_current_user
    ] = lambda: current_user

    yield client

    app.dependency_overrides.clear()

@pytest.fixture
def current_user():
    return User(
        id=1,
        username="deadpool",
        email="deadpool@example.com",
        confirmed=True,
        created_at=datetime.now(),
        avatar="old_avatar.jpg",
    )

@pytest.fixture
def contact(current_user):
    return Contact(
        id=1,
        first_name="Nazar",
        last_name="Boyko",
        email="nazar@test.com",
        phone="+380991234567",
        birthday="2000-05-10",
        additional_information="Test contact",
        user_id=current_user.id,
    )

@pytest.fixture(scope="module")
def user():
    return {
        "id": 1,
        "username": "deadpool",
        "email": "deadpool@example.com",
        "password": "123456789",
        "created_at": "2026-09-21T12:00:00",
        "confirmed": True,
        "avatar": "https://example.com/avatar.jpg",
    }
