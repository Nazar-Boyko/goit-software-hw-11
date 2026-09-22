from sqlalchemy.orm import Session
from libgravatar import Gravatar

from src.database.models import User
from src.schemas import UserModel



async def get_user_by_email(email: str, db: Session) -> User | None:

    """ 
    Retrieves a user from the database based on their email address.

    :param email: The email of the user to retrive
    :type email: str
    :param db: The database session
    :type db: Session
    :return: The user with specified email, or None if it does not exist
    :rtype: User | None
    """
    return db.query(User).filter(User.email == email).first()

async def create_user(body: UserModel, db: Session) -> User:

    """
    Create a new user in the database with the provided user data.

    :param body: The data for the user to create
    :type body: UserModel
    :param db: The database session
    :type db: Session
    :return: The newly created user
    :rtype: User
    """

    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.dict(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

async def update_token(user: User, token: str | None, db: Session) -> None:

    """
    Updates the refresh token for a specific user in the database.

    :param user: The user to update the refresh token for.
    :type user: User
    :param token: The new refresh token to set for the user, or None to clear it.
    :type token: str | None
    :param db: The database session.
    :type db: Session
    :return: None
    :rtype: None
    """
    user.refresh_token = token
    db.commit()

async def confirmed_email(email: str, db: Session) -> None:

    """
    Confirms the email address for a user in the database.

    :param email: The email of the user to confirm
    :type email: str
    :param db: The database session
    :type db: Session
    :return: None
    :rtype: None
    """
    user = await get_user_by_email(email, db)
    if user is None:
        return
    user.confirmed = True
    db.commit()

async def update_avatar(email: str, src_url: str, db: Session) -> User:

    """
    Updates the avatar URL for a specific user in the database.
    
    :param email: The email of the user to update
    :type email: str
    :param src_url: The new avatar URL to set for the user
    :type src_url: str
    :param db: The database session
    :type db: Session
    :return: The updated user
    :rtype: User
    """ 
    user = await get_user_by_email(email, db)

    if user is None:
        return
    
    user.avatar = src_url
    db.commit()
    return user