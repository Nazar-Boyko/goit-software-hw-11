import unittest
from unittest.mock import MagicMock, patch, AsyncMock


from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_avatar,
    update_token,
    confirmed_email,

)


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session: Session = MagicMock(spec=Session)
        self.user = User(
            id=1,
            username="testy",
            email="test@test.com",
            password="test123",
        )

    async def test_get_user_by_email(self):

        user = User(
            id=1,
            username="testy",
            email="test@test.com",
            password="test123",
        )

        self.session.query().filter().first.return_value = user

        result = await get_user_by_email(
            email='test@test.com',
            db=self.session
        )

        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):

        self.session.query().filter().first.return_value = None

        result = await get_user_by_email(
            email='test@test.com',
            db=self.session
        )

        self.assertIsNone(result)

    async def test_create_user(self):

        mock_gravatar = MagicMock()

        mock_gravatar.get_image.return_value = (
            "https://example.com/avatar.jpg")

        with patch(
            "src.repository.users.Gravatar",
            return_value=mock_gravatar,
        ) as mock_gravatar_class:
            body = UserModel(
                username="testy",
                email="test@test.com",
                password="test123",
            )

            result = await create_user(
                body=body,
                db=self.session
            )

        self.session.add.assert_called_once_with(result)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(result)

        self.assertEqual(result.email, body.email)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.password, body.password)
        self.assertEqual(result.avatar, "https://example.com/avatar.jpg")
        self.assertTrue(hasattr(result, "id"))

        mock_gravatar_class.assert_called_once_with(body.email)

        mock_gravatar.get_image.assert_called_once()

    async def test_update_avatar_found(self):

        new_avatar = 'new_avatar'

        with patch(
            "src.repository.users.get_user_by_email",
            new_callable=AsyncMock,
            return_value=self.user,
        ) as mock_get_user:

            result = await update_avatar(
                email="test@test.com",
                src_url=new_avatar,
                db=self.session
            )

        self.assertEqual(result, self.user)
        self.assertEqual(result.avatar, new_avatar)
        mock_get_user.assert_called_once_with(
            "test@test.com",
            self.session,
        )

        self.session.commit.assert_called_once()

    async def test_update_avatar_not_found(self):

        new_avatar = 'new_avatar'
        with patch(
            "src.repository.users.get_user_by_email",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get_user:

            result = await update_avatar(
                email="unknown@test.com",
                src_url=new_avatar,
                db=self.session,
            )

        self.assertIsNone(result)
        self.session.commit.assert_not_called()

    async def test_create_user_gravatar_error(self):

        mock_gravatar = MagicMock()
        mock_gravatar.get_image.side_effect = Exception("Gravatar error")

        with patch(
            "src.repository.users.Gravatar",
            return_value=mock_gravatar,
        ):
            body = UserModel(
                username="testy",
                email="test@test.com",
                password="test123",
            )

            result = await create_user(
                body=body,
                db=self.session
            )

        self.assertIsNone(result.avatar)
        self.session.add.assert_called_once_with(result)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(result)

    async def test_confirmed_email_user_found(self):

        with patch(
            "src.repository.users.get_user_by_email",
            new_callable=AsyncMock,
            return_value=self.user,
        ) as mock_get_user:

            result = await confirmed_email(
                email="test@test.com",
                db=self.session
            )

        self.assertIsNone(result)
        self.assertTrue(self.user.confirmed)

        mock_get_user.assert_called_once_with(
            "test@test.com",
            self.session,
        )

        self.session.commit.assert_called_once()

    async def test_confirmed_email_user_not_found(self):

        with patch(
            "src.repository.users.get_user_by_email",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get_user:

            result = await confirmed_email(
                email="unknown@test.com",
                db=self.session,
            )

        self.assertIsNone(result)
        self.session.commit.assert_not_called()

    async def test_update_token(self):
        token = "new_refresh_token"

        result = await update_token(
            user=self.user,
            token=token,
            db=self.session
        )

        self.assertIsNone(result)
        self.assertEqual(self.user.refresh_token, token)
        self.session.commit.assert_called_once()
