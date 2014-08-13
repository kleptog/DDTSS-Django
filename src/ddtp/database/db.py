"""
DDTSS-Django - A Django implementation of the DDTP/DDTSS website.
Copyright (C) 2011-2014 Martijn van Oosterhout <kleptog@svana.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import functools

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from django.conf import settings
# Import the logging library.
import logging


Base = declarative_base()

# Set SQL-Alchemy logging.
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

Session = None

def get_db_session():
    # create a configured "Session" class
    global Session
    if not Session:
        db_engine = sqlalchemy.create_engine(URL(**settings.DDTP_DATABASE))
        Session = sessionmaker(bind=db_engine)
    # create a Session
    return Session()

def with_db_session(view):
    """ Decorator that provides a session argument and cleans up on return """
    @functools.wraps(view)
    def new_view(*args, **kwargs):
        try:
            session = get_db_session()
            return view(session, *args, **kwargs)
        finally:
            session.close()
    return new_view
