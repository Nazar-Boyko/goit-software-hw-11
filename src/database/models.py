
from sqlalchemy import Column, Integer, String, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Date, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

# Ім'я
# Прізвище
# Електронна адреса
# Номер телефону
# День народження


class Contaсt(Base):

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)

    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(50), nullable= False)

    birthday = Column(Date, nullable = False )

    additional_information = Column(String(500))

    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), default=None)
    user = relationship("User", backref='contacts')


class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    username = Column(String(50))
    email = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)

    created_at =Column('created_at', DateTime, default=func.now())
    refresh_token = Column(String(255), nullable=True)

    
