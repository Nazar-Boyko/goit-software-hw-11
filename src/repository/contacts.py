from typing import List

from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactBase

from datetime import date, timedelta

async def get_contacts(skip: int, limit: int, user: User, db: Session) -> List[Contact]:

    '''
    Retrives a list of contacts for a specific user with specified pagination parameters.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param user: The user to retrive contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[Contact]
    '''
    return db.query(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit).all()

async def get_contact(contact_id: int, user: User, db: Session) -> Contact:

    """
    Retrives a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the note to retrive.
    :type contect_id: int
    :param user: The userr to retrieve the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The contact with the specified ID, or None if in does not exist
    :rtype: Contact | None
    """
    return db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()


async def search_contacts(
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    user: User,
    db: Session
    ) -> List[Contact]:

    """
    Searches for contacts based on the provided search criteria (first name, last name, and email) for a specific user.

    :param first_name: The first name to search for (optional).
    :type firts_name: str | None
    :param last_name: The last name to search for (optional).
    :type last_name: str | None
    :param email: The email to search for (optional)
    :type email: str | None
    :param user: The user to search contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts matching the search criteria.
    :rtype: List[Contact]

    """

    query = db.query(Contact).filter(Contact.user_id == user.id)

    if first_name:
        query = query.filter(
            Contact.first_name.ilike(f"%{first_name}%")
        )

    if last_name:
        query = query.filter(
            Contact.last_name.ilike(f"%{last_name}%")
        )

    if email:
        query = query.filter(
            Contact.email.ilike(f"%{email}%")
        )

    return query.all()

async def get_upcoming_birthdays(skip: int, limit: int, user: User, db : Session) -> List[Contact] | None:

    """
    Retrieves a list of contacts with upcoming birthdays within the next 7 days for a specific user.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param user: The user to retrive contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts or None if does not exist.
    :rtype: List[Contact]
    """

    days = 7

    upcoming_birthdays = []
    today = date.today()
    end_date = today + timedelta(days=days)

    contacts = await get_contacts(skip, limit, user, db)

    for contact in contacts:

        birthday = contact.birthday

        birthday_this_year = birthday.replace(year=today.year)

        if birthday_this_year < today:
            birthday_this_year = birthday_this_year.replace(year=today.year + 1)
        
        if today <= birthday_this_year <= end_date:
            upcoming_birthdays.append(contact)
    return upcoming_birthdays


async def create_contact(body: ContactBase, user: User, db: Session) -> Contact:

    """
    Creates a new contact for a specific user.

    :param body: The data for the contact to create.
    :type body: ContactBase
    :param user: The user to create the contact for
    :type user: User
    :param db: The databse session.
    :type db: Session
    :return: The newly created contact
    :rtype: Contact
    """

    

    contact = Contact(**body.model_dump(), user_id = user.id)

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact

async def update_contact(contact_id: int, body: ContactBase, user: User, db: Session) -> Contact | None:

    """
    Update a single contact with the specified Id for a specific user.

    :param contact_id: The ID of the contact to update
    :type contact_id: int
    :param user: The user to update the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact, or None if it does not exist.
    :rtype: Contact | None
    """

    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()

    if contact:
        for field, value in body.model_dump().items():
            setattr(contact, field, value)

        db.commit()
        db.refresh(contact)

        return contact

    return None

async def remove_contact(contact_id: int, user: User, db: Session) -> Contact | None:

    """
    Removes a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to remove
    :type contact_id: int
    :param user: The user to remove the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The removed contact, or None if it does not exist.
    :rtype: Contact | None
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if contact:
        db.delete(contact)
        db.commit()

    return contact
        
