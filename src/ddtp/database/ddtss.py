# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import re
import time
import difflib

from .db import Base, with_db_session
from .ddtp import Description
from django.conf import settings
from sqlalchemy.orm import relationship, collections
from sqlalchemy.orm.session import Session
from sqlalchemy import Table, Column, Integer, String, Date, Boolean, MetaData, ForeignKey, FetchedValue, Sequence, text

# __/config/*
class Languages(Base):
    """ Each language also has metainfo """
    __tablename__ = 'languages_tb'

    language = Column(String, primary_key=True)
    fullname = Column(String, nullable=False)
    numreviewers = Column(Integer, nullable=False)
    requirelogin = Column(Boolean, nullable=False, default=False)
    enabled_ddtss = Column(Boolean, nullable=False, default=True)  # disabled

# /aliases/*
class Users(Base):
    """ Each user which can login has a record """
    __tablename__ = 'users_tb'

    username = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    realname = Column(String)
    active = Column(Boolean, nullable=False)
    countreviews = Column(Integer, nullable=False, default=0)
    counttranslations = Column(Integer, nullable=False, default=0)
    key = Column(String, nullable=False)
    md5password = Column(String, nullable=False)
    lastseen = Column(Integer, nullable=False)   # timestamp
    lastlanguage_ref = Column('lastlanguage', String, ForeignKey('languages_tb.language'))
    superuser = Column(Boolean, nullable=False, default=False)

    lastlanguage = relationship(Languages)

    # A user from the database is by default logged. The login process will
    # ensure that this field is reset in instances where the user is not a
    # real user (just IP address).
    logged_in = True

# __/done/*  Log of results, do we want this? Only submitter/reviewer info
# __/logs/*  Logs of email comms, not needed

class PendingTranslation(Base):
    """ A translation that is in the process of being translated """
    __tablename__ = 'pendingtranslations_tb'

    # Manually created sequence it necessary as SQLalchemy believes SERIAL is only useful for primary keys
    pending_translation_id = Column(Integer,
                                    Sequence('pendingtranslations_tb_pending_translation_id_seq'),
                                    server_default=text("nextval('pendingtranslations_tb_pending_translation_id_seq')"),
                                    unique=True, nullable=False)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), primary_key=True)
    language_ref = Column('language', String, ForeignKey('languages_tb.language'), primary_key=True)

    language = relationship(Languages, backref="pending_translations")

    comment = Column(String)
    # data not needed
    log = Column(String)  # More useful format?
    firstupdate = Column(Integer, nullable=False)  # age
    long = Column(String)
    short = Column(String)
    oldlong = Column(String)
    oldshort = Column(String)
    lastupdate = Column(Integer, nullable=False)  # timestamp
    owner_username = Column(String)               # NULL if no owner, could be IP for anonymous
    owner_locktime = Column(Integer)              # Timestamp that owner "locked" this description, NULL if not locked
    iteration = Column(Integer, nullable=False)   # Iteration
    state = Column(Integer, nullable=False)       # One of the states below

    user = relationship(Users, primaryjoin=(owner_username == Users.username), foreign_keys=[owner_username], uselist=False)
    description = relationship(Description, backref='pending_translations')

    STATE_PENDING_TRANSLATION = 0
    STATE_PENDING_REVIEW = 1

    @classmethod
    def make_suggestion(self, description, language):
        """ From a description object and a language, make a suggestion for
        the description using existing parts """

        parts = description.get_description_part_objects()
        # A map from untranslated text, to translated text
        fuzzy_parts = dict( description.get_potential_fuzzy_matches(language) )
        suggest = []
        for text, hash, part in parts:
            if part and language in part.translation:
                suggest.append(part.translation[language].part)
            else:
                # Look for the nearest fuzzy match, and if exists
                match = difflib.get_close_matches(text, fuzzy_parts.iterkeys(), 1, 0.8)
                if match:
                    suggest.append(u" <fuzzy>\n" + fuzzy_parts[match[0]].part)
                else:
                    suggest.append(u" <trans>\n")
        return suggest[0], " .\n".join(suggest[1:])

    # Methods for handling the optimistic locking
    def is_locked(self):
        """ True if record is (optimistically) locked """
        now = time.time()
        return self.owner_locktime and self.owner_locktime > now - settings.DDTSS_LOCK_TIMEOUT

    def trylock(self, user):
        """ Check if this translation can be locked or is locked by this
        user, and acquire lock if possible.  Returns True if lock acquired.
        To protect against concurrency issues, the record should be selected
        FOR UPDATE """

        if self.is_locked() and self.owner_username != user.username:
            return False

        self.owner_username = user.username
        self.owner_locktime = int(time.time())
        return True

    def unlock(self):
        """ Remove lock from record """
        self.owner_locktime = None
        return

    # Display methods
    #
    # When editting we make slight changes to the text we display.
    #
    #    - Remove the leading space from the long description.
    #
    #    - Replace the non-breaking space (U+00A0) with middot (U+00B7)
    #      because browsers otherwise lose it.
    #
    def display_long(self):
        """ Convert long for display """
        return self.for_display(self.long)

    def display_short(self):
        """ Convert long for display """
        return self.for_display(self.short)

    def for_display(self, s):
        """ Convert string for display """
        s = re.sub("(?m)^ ", "", s)
        s = s.replace(u"\r", u"")
        s = s.replace(u"\u00A0", u"\u00B7")
        return s

    def from_display(self, s):
        """ Convert string in display back to normal """
        s = re.sub("(?m)^", " ", s)
        s = s.replace(u"\r", u"")
        s = s.replace(u"\u00B7", u"\u00A0")
        return s

    # Update translation
    def update_translation(self, short, long):
        # FIXME: Check new description has correct numer of paragraphs
        # FIXME: Logging of changes
        change = False

        newshort = self.from_display(short)
        if self.short != newshort:
            self.oldshort = self.short
            self.short = newshort
            change = True

        newlong = self.from_display(long)
        if self.long != newlong:
            self.oldlong = self.long
            self.long = newlong
            change = True

        if change:
            self.lastupdate = int(time.time())
            self.iteration += 1

        if ('<trans>' not in short and '<trans>' not in long and
            '<fuzzy>' not in short and '<fuzzy>' not in long):
            self.state = PendingTranslation.STATE_PENDING_REVIEW

        return

class PendingTranslationReview(Base):
    """ A review of a translation """
    __tablename__ = 'pendingtranslationreview_tb'

    pending_translation_id = Column(Integer, ForeignKey('pendingtranslations_tb.pending_translation_id'), primary_key=True)
    username = Column(String, primary_key=True)

    user = relationship(Users, primaryjoin=(username == Users.username), foreign_keys=[username], uselist=False)
    translation = relationship(PendingTranslation, backref='reviews')

    # In the future we might have different kinds of review, we could store
    # that data here

class Messages(Base):
    """ Messages, global, user or language """
    __tablename__ = 'messages_tb'

    message_id = Column(Integer, primary_key=True, autoincrement=True)

    # Specify who sees it:
    # Both NULL: global
    # Language: for that language only
    # User: for that user only
    # Both: Not allowed
    language = Column(String, ForeignKey('languages_tb.language'))
    to_user = Column(String, ForeignKey('users_tb.username'))

    from_user =  Column(String, ForeignKey('users_tb.username'), nullable=False)
    timestamp = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
