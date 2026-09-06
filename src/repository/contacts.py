from typing import List

from sqlalchemy.orm import Session

from src.database.models import Contaсt, User
from src.schemas import ContactBase

from datetime import date, timedelta

async def get_contacts(skip: int, limit: int, user: User, db: Session) -> List[Contaсt]:
    return db.query(Contaсt).filter(Contaсt.user_id == user.id).offset(skip).limit(limit).all()

async def get_contact(contact_id: int, user: User, db: Session) -> Contaсt:
    return db.query(Contaсt).filter(Contaсt.id == contact_id, Contaсt.user_id == user.id).first()


async def search_contacts(
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    user: User,
    db: Session
    ) -> List[Contaсt]:

    query = db.query(Contaсt).filter(Contaсt.user_id == user.id)

    if first_name:
        query = query.filter(
            Contaсt.first_name.ilike(f"%{first_name}%")
        )

    if last_name:
        query = query.filter(
            Contaсt.last_name.ilike(f"%{last_name}%")
        )

    if email:
        query = query.filter(
            Contaсt.email.ilike(f"%{email}%")
        )

    return query.all()

async def get_upcoming_birthdays(skip: int, limit: int, user: User, db : Session):

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


async def create_contact(body: ContactBase, user: User, db: Session) -> Contaсt:

    contact = Contaсt(**body.model_dump(), user_id = user.id)

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact

async def update_contact(contact_id: int, body: ContactBase, user: User, db: Session) -> Contaсt | None:

    contact = db.query(Contaсt).filter(Contaсt.id == contact_id, Contaсt.user_id == user.id).first()

    if contact:
        for field, value in body.model_dump().items():
            setattr(contact, field, value)

        db.commit()
        db.refresh(contact)

        return contact

    return None

async def remove_contact(contact_id: int, user: User, db: Session) -> Contaсt | None:

    contact = db.query(Contaсt).filter(Contaсt.id == contact_id, Contaсt.user_id == user.id).first()
    if contact:
        db.delete(contact)
        db.commit()

    return contact
        
