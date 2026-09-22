from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Rate, Duration, Limiter
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import ContactBase, ContactResponse
from src.repository import contacts as contacts_repository
from src.services.auth import auth_service
from src.database.models import User


router = APIRouter(
    prefix="/contacts",
    tags=["contacts"]
)

contacts_rate_limiter = RateLimiter(
    limiter=Limiter(
        Rate(10, Duration.MINUTE)
    )
)

@router.get(
    "/",
    response_model=List[ContactResponse],
    description="No more than 10 request per minute", 
    dependencies=[
        Depends(
            contacts_rate_limiter
        )
    ]
)
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):

    """
    Retrieves a list of contacts for the current user with specified pagination parameters.
    
    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[ContactResponse]

    """

    contacts = await contacts_repository.get_contacts(
        skip,
        limit,
        current_user,
        db
    )
    return contacts


@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Searches for contacts based on the provided criteria.

    :param first_name: The first name to search for.
    :type first_name: str | None
    :param last_name: The last name to search for.
    :type last_name: str | None
    :param email: The email to search for.
    :type email: str | None
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts matching the search criteria.
    :rtype: List[ContactResponse]
    """
    return await contacts_repository.search_contacts(
        first_name,
        last_name,
        email,
        current_user,
        db
    )


@router.get(
    "/upcoming_birthday",
    response_model=List[ContactResponse]
)
async def get_upcoming_birthday(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):

    """
    Retrieves a list of contacts with upcoming birthdays for the current user.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[ContactResponse]
    """

    return await contacts_repository.get_upcoming_birthdays(
        skip,
        limit,
        current_user,
        db
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a specific contact by ID.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The requested contact.
    :rtype: ContactResponse
    """

    contact = await contacts_repository.get_contact(
        contact_id,
        current_user,
        db
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return contact


@router.post(
    "/",
    response_model=ContactResponse, 
    status_code=status.HTTP_201_CREATED,
    description="No more than 10 contacts per minute",
    dependencies=[
        Depends(
            contacts_rate_limiter
        )
    ]
)
async def create_contact(
    body: ContactBase,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new contact for the current user.

    :param body: The details of the contact to create.
    :type body: ContactBase
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The created contact.
    :rtype: ContactResponse
    """
    return await contacts_repository.create_contact(
        body,
        current_user,
        db
    )


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactBase,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates an existing contact for the current user.
    
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated details of the contact.
    :type body: ContactBase
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact.
    :rtype: ContactResponse
    
    """
    contact = await contacts_repository.update_contact(
        contact_id,
        body,
        current_user,
        db
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(
    contact_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a contact by ID.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The removed contact.
    :rtype: ContactResponse
    """
    contact = await contacts_repository.remove_contact(
        contact_id,
        current_user,
        db
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return contact
