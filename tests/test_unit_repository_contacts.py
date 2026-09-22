import unittest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactBase
from src.repository.contacts import (
    get_contact,
    get_contacts,
    create_contact,
    remove_contact,
    update_contact,
    get_upcoming_birthdays,
    search_contacts,
)


class TestContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session: Session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact(), Contact(), Contact()]

        self.session.query().filter().offset().limit().all.return_value = contacts

        result = await get_contacts(
            skip=0,
            limit=10,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = Contact()

        self.session.query().filter().first.return_value = contact

        result = await get_contact(
            contact_id=1,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        self.session.query().filter().first.return_value = None

        result = await get_contact(
            contact_id=1,
            user=self.user,
            db=self.session
        )

        self.assertIsNone(result)

    async def test_search_contacts_by_first_name(self):
        contacts = [
            Contact(
                id=1,
                first_name="test",
                user_id=1,
            )
        ]

        self.session.query().filter().filter().all.return_value = contacts

        result = await search_contacts(
            first_name="test",
            last_name=None,
            email=None,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contacts)

    async def test_search_contacts_by_last_name(self):
        contacts = [
            Contact(
                id=1,
                last_name="test",
                user_id=1,
            )
        ]

        self.session.query().filter().filter().all.return_value = contacts

        result = await search_contacts(
            first_name=None,
            last_name="test",
            email="",
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contacts)

    async def test_search_contacts_by_email(self):
        contacts = [
            Contact(
                id=1,
                email="test@test.com",
                user_id=1,
            )
        ]

        self.session.query().filter().filter().all.return_value = contacts

        result = await search_contacts(
            first_name=None,
            last_name=None,
            email="test@test.com",
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contacts)

    async def test_search_contacts_without_arguments(self):
        contacts = [
            Contact(id=1, first_name="Test1", user_id=1),
            Contact(id=2, first_name="Test2", user_id=1),
        ]

        self.session.query().filter().all.return_value = contacts

        result = await search_contacts(
            first_name=None,
            last_name=None,
            email=None,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contacts)

    async def test_search_contacts_by_first_name_not_found(self):
        self.session.query().filter().filter().all.return_value = []

        result = await search_contacts(
            first_name="Unknown",
            last_name=None,
            email=None,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, [])

    async def test_search_contacts_by_last_name_not_found(self):
        self.session.query().filter().filter().all.return_value = []

        result = await search_contacts(
            first_name=None,
            last_name="Unknown",
            email=None,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, [])

    async def test_search_contacts_by_email_not_found(self):
        self.session.query().filter().filter().all.return_value = []

        result = await search_contacts(
            first_name=None,
            last_name=None,
            email="unknown@test.com",
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, [])

    async def test_get_upcoming_birthdays(self):
        today = date.today()

        contact = Contact(
            id=1,
            first_name="Test",
            last_name="test",
            email="test@test.com",
            birthday=today + timedelta(days=3),
            user_id=self.user.id
        )

        with patch(
            "src.repository.contacts.get_contacts",
            return_value=[contact]
        ):
            result = await get_upcoming_birthdays(
                skip=0,
                limit=10,
                user=self.user,
                db=self.session
            )

        self.assertEqual(result, [contact])

    async def test_get_upcoming_birthdays_not_found(self):
        today = date.today()

        contact = Contact(
            id=1,
            first_name="Test",
            last_name="test",
            email="test@test.com",
            birthday=today + timedelta(days=10),
            user_id=self.user.id
        )

        with patch(
            "src.repository.contacts.get_contacts",
            return_value=[contact]
        ):
            result = await get_upcoming_birthdays(
                skip=0,
                limit=10,
                user=self.user,
                db=self.session
            )

        self.assertEqual(result, [])

    async def test_get_upcoming_birthdays_empty(self):
        with patch(
            "src.repository.contacts.get_contacts",
            return_value=[]
        ):
            result = await get_upcoming_birthdays(
                skip=0,
                limit=10,
                user=self.user,
                db=self.session
            )

        self.assertEqual(result, [])

    async def test_get_upcoming_birthdays_today(self):
        today = date.today()

        contact = Contact(
            id=1,
            first_name="Nazar",
            last_name="Boyko",
            email="nazar@test.com",
            birthday=today,
            user_id=self.user.id
        )

        with patch(
            "src.repository.contacts.get_contacts",
            return_value=[contact]
        ):
            result = await get_upcoming_birthdays(
                skip=0,
                limit=10,
                user=self.user,
                db=self.session
            )

        self.assertEqual(result, [contact])

    async def test_get_upcoming_birthdays_birthday_already_passed(self):
        today = date.today()

        contact = Contact(
            id=1,
            first_name="Nazar",
            last_name="Boyko",
            email="nazar@test.com",
            birthday=date(2000, today.month, today.day - 1),
            user_id=self.user.id
        )

        with patch(
            "src.repository.contacts.get_contacts",
            return_value=[contact]
        ):
            result = await get_upcoming_birthdays(
                skip=0,
                limit=10,
                user=self.user,
                db=self.session
            )

        self.assertEqual(result, [])

    async def test_create_contact(self):
        body = ContactBase(
            first_name="test",
            last_name="test",
            email="test@test.com",
            phone="06893939507",
            birthday="2000-10-13",
            additional_information="test information",
            
            
        )

        result = await create_contact(
            body=body,
            user=self.user,
            db=self.session
        )

        self.session.add.assert_called_once_with(result)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(result)

        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.user_id, self.user.id)
        self.assertTrue(hasattr(result, "id"))

    async def test_remove_contact_found(self):
        contact = Contact()

        self.session.query().filter().first.return_value = contact

        result = await remove_contact(
            contact_id=1,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contact)
        self.session.delete.assert_called_once_with(contact)
        self.session.commit.assert_called_once()

    async def test_remove_contact_not_found(self):
        self.session.query().filter().first.return_value = None

        result = await remove_contact(
            contact_id=1,
            user=self.user,
            db=self.session
        )

        self.assertIsNone(result)

    async def test_update_contact_found(self):
        contact = Contact()

        self.session.query().filter().first.return_value = contact

        body = ContactBase(
            first_name="updated",
            last_name="updated",
            email="updated@test.com",
            phone="06893939507",
            birthday="2000-10-13",
            additional_information="updated information",
            
        )


        result = await update_contact(
            contact_id=1,
            body=body,
            user=self.user,
            db=self.session
        )

        self.assertEqual(result, contact)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(contact)

    async def test_update_contact_not_found(self):
        body = ContactBase(
            first_name="updated",
            last_name="updated",
            email="updated@test.com",
            phone="06893939507",
            birthday="2000-10-13",
            additional_information="updated information",
        )

        self.session.query().filter().first.return_value = None

        result = await update_contact(
            contact_id=1,
            body=body,
            user=self.user,
            db=self.session
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
