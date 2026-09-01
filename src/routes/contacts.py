from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import ContactBase, ContactResponse
from src.repository import contacts as contacts_repository

router = APIRouter(prefix='/contacts', tags = ["contacts"])

@router.get("/", response_model=List[ContactResponse])
async def read_contacts(
    skip:int = 0, 
    limit:int = 100, 
    db:Session = Depends(get_db)):

    contacts = await contacts_repository.get_contacts(skip, limit, db)
    return contacts


@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    db: Session = Depends(get_db)
    ):

    return await contacts_repository.search_contacts(
        first_name,
        last_name,
        email,
        db
    )

@router.get("/upcoming_birthday", response_model=List[ContactResponse])
async def get_aucomaing_birthday(
    skip: int = 0,
    limit: int = 100,
    db : Session = Depends(get_db)
    ):

    return await contacts_repository.get_upcoming_birthdays(skip, limit, db)

@router.get('/{contact_id}', response_model=ContactResponse)
async def read_contact(
    contact_id: int, 
    db: Session = Depends(get_db)):

    contact = await contacts_repository.get_contact(contact_id, db)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return contact




@router.post("/", response_model=ContactResponse)
async def create_contact(
    body: ContactBase, 
    db: Session = Depends(get_db)):

    return await contacts_repository.create_contact(body,db)

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactBase,
    db: Session = Depends(get_db)
    ):

    contact = await contacts_repository.update_contact(contact_id, body, db)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Contact not found')

    return contact

@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(
    contact_id: int,
    db: Session = Depends(get_db)):

    contact = await contacts_repository.remove_contact(contact_id, db)

    if contact is None:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Contact not found')

    return contact