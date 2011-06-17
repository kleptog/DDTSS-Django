from .db import Base, get_db_session
from .ddtp import Description
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

    lastlanguage = relationship(Languages)

# __/done/*  Log of results, do we want this? Only submitter/reviewer info
# __/logs/*  Logs of email comms, not needed

class PendingTranslation(Base):
    """ A translation that is in the process of being translated """
    __tablename__ = 'pendingtranslations_tb'

    # Manually created sequence it necessary as SQLalchemy beleives SERIAL is only useful for primary keys
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
    iteration = Column(Integer, nullable=False)   # iter
    owner_username = Column(String)               # NULL if no owner, could be IP for anonymous
    state = Column(Integer, nullable=False)

    user = relationship(Users, primaryjoin=(owner_username == Users.username), foreign_keys=[owner_username], uselist=False)
    description = relationship(Description, backref='pending_translations')

    STATE_PENDING_TRANSLATION = 0
    STATE_PENDING_REVIEW = 1

    @classmethod
    def make_suggestion(self, description, language):
        """ From a description object and a language, make a suggestion for
        the description using existing parts """

        parts = description.get_description_part_objects()
        suggest = []
        for text, hash, part in parts:
            if part and language in part.translation:
                suggest.append(part.translation[language].part)
            else:
                suggest.append(' <trans>\n')
        return suggest[0], " .\n".join(suggest[1:])

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
