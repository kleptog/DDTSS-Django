import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from django.conf import settings

Base = declarative_base()

Session = None

def get_db_session():
    # create a configured "Session" class
    global Session
    if not Session:
       db_engine = sqlalchemy.create_engine(URL(**settings.DDTP_DATABASE), echo=settings.DEBUG)
       Session = sessionmaker(bind=db_engine)
    # create a Session
    return Session()
