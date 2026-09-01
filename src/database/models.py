
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Date
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
