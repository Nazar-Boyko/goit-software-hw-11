from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv
from src.conf.config import settings

import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

    
