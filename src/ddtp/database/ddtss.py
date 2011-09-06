# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import re
import hmac
import time
import difflib

from .db import Base, with_db_session
from .ddtp import Description, DescriptionMilestone, Translation, PartDescription, Part, description_to_parts, Statistic
from django.conf import settings
from django.utils.timesince import timesince
from sqlalchemy import types
from sqlalchemy.orm import relationship, collections, backref, relation, aliased
from sqlalchemy.orm.session import Session
from sqlalchemy import Table, Column, Integer, String, Date, Boolean, MetaData, ForeignKey, FetchedValue, Sequence, text
from datetime import datetime

class TranslationModel(object):
    """ Represents a model used to control the model used for translating """

    models = dict()
    model_name = ''

    ACTION_TRANSLATE = 0
    ACTION_REVIEW = 1

    # These are serialisation and deserialisation to the database. The A is
    # in case we support multiple models in the future.
    def to_string(self):
        assert False, "Not implemented"

    @classmethod
    def from_string(cls, s):
        type = s[0]
        if type in cls.models:
            return cls.models[type].from_string(s)
        raise Exception("Unknown translation accept model %s" % type)

    @classmethod
    def register_model(cls, model):
        assert len(model.model_name) == 1, "Model name must be single character"
        cls.models[model.model_name] = model

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.to_string())

    def user_allowed(self, user, language, action):
        """ Returns true of user is permitted to do action """
        # user is User object
        # action is one of the ACTION_* constants in this class
        assert False, "Not implemented"

    def translation_accepted(self, translation):
        """ Returns true if translation is accepted """
        # translation is PendingTranslation object
        assert False, "Not implemented"

class TranslationModelType(types.TypeDecorator):
    """ Represents the translation from the model in the database to in memory """

    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return value.to_string()

    def process_result_value(self, value, dialect):
        return TranslationModel.from_string(value)

# __/config/*
class Languages(Base):
    """ Each language also has metainfo """
    __tablename__ = 'languages_tb'

    language = Column(String, primary_key=True)
    fullname = Column(String, nullable=False)
    enabled_ddtss = Column(Boolean, nullable=False, default=True)  # disabled
    translation_model = Column(TranslationModelType, nullable=False)
    milestone_high = Column(String, ForeignKey('description_milestone_tb.milestone'))
    milestone_medium = Column(String, ForeignKey('description_milestone_tb.milestone'))
    milestone_low = Column(String, ForeignKey('description_milestone_tb.milestone'))

    @property
    def coordinators(self):
        """ Returns the coordinators for this language """
        return Session.object_session(self).query(Users).join(UserAuthority).\
                filter(UserAuthority.language_ref==self.language).\
                filter(UserAuthority.auth_level==UserAuthority.AUTH_LEVEL_COORDINATOR).all()

    @property
    def trusted_users(self):
        """ Returns the coordinators for this language """
        return Session.object_session(self).query(Users).join(UserAuthority).\
                filter(UserAuthority.language_ref==self.language).\
                filter(UserAuthority.auth_level==UserAuthority.AUTH_LEVEL_TRUSTED).all()

    def __repr__(self):
        return '<Languages %s (%s)>' % (self.language, self.fullname)

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
    milestone = Column(String, ForeignKey('description_milestone_tb.milestone'))

    lastlanguage = relationship(Languages)

    # A user from the database is by default logged. The login process will
    # ensure that this field is reset in instances where the user is not a
    # real user (just IP address).
    logged_in = True

    # These are methods to handle the information transfer between cookies and user objects
    def to_cookie(self):
        """ Creates the cookie contents for this user """
        s = "%s:%d:%d:%s" % (self.username, self.countreviews, self.counttranslations, self.lastlanguage_ref)
        digest = hmac.new(settings.SECRET_KEY, s).hexdigest()

        return digest + "|" + s

    @classmethod
    def from_cookie(self, cookie):
        """ Given the cookie content, verifies it and returns a user object """
        digest, _, s = cookie.partition("|")
        if not digest or not s:
            return None
        if hmac.new(settings.SECRET_KEY, s).hexdigest() != digest:
            return None

        # Received signed cookie, parse it into new user object
        v = s.split(":")
        return Users(username=v[0],
                    countreviews=int(v[1]),
                    counttranslations=int(v[2]),
                    logged_in=False,
                    lastlanguage_ref=v[3])

    def Get_flot_data(self):
        """ Returns all versions in a nice format """

        max_counter=100

        session = Session.object_session(self)

        if not session:
            # Anonymous user, no stats recorded. Queries below won't work
            # because the user doesn't exist in database and hence no
            # session object.
            output_prozt = "var quote=[];"
            output_total = "var trans=[];"
            output_trans = "var revie=[];"

            return output_prozt+output_total+output_trans

        values = list();
        Statistic2 = aliased(Statistic)
        values = session.query(Statistic2.value*1000/Statistic.value, Statistic.value, Statistic2.value). \
                filter(Statistic.stat == 'user:translations-'+self.username). \
                filter(Statistic2.stat == 'user:reviews-'+self.username). \
                filter(Statistic.date == Statistic2.date). \
                order_by(Statistic.date.asc()). \
                limit(max_counter). \
                all()
        output_prozt = "var quote=%s;" % ([[i, stat[0]/10] for i, stat in enumerate(values)]) 
        output_total = "var trans=%s;" % ([[i, stat[1]] for i, stat in enumerate(values)])    
        output_trans = "var revie=%s;" % ([[i, stat[2]] for i, stat in enumerate(values)])

        return output_prozt+output_total+output_trans

    def get_authority(self, language):
        """ Get authority object """
        # If user is not persistant, no authority
        session = Session.object_session(self)
        if not session:
            return UserAuthority(username=self.username, language_ref=language, auth_level=UserAuthority.AUTH_LEVEL_NONE)
        # Otherwise check authority record
        auth = session.query(UserAuthority).filter_by(username=self.username, language_ref=language).first()
        if not auth:
            return UserAuthority(username=self.username, language_ref=language, auth_level=UserAuthority.AUTH_LEVEL_NONE)
        return auth

    @property
    def is_trusted(self):
        return self.get_authority(self.lastlanguage_ref).is_trusted

    @property
    def is_coordinator(self):
        return self.get_authority(self.lastlanguage_ref).is_coordinator

    def __repr__(self):
        return '<Users %s (%s)>' % (self.username, self.email)

class UserAuthority(Base):
    """ Stores the trust level of each user for each language """
    __tablename__ = 'userauthority_tb'

    username = Column(String, ForeignKey('users_tb.username'), primary_key=True)
    language_ref = Column('language', String, ForeignKey('languages_tb.language'), primary_key=True)

    # For now all we have is a level. What you can do with each level is
    # defined elsewhere.
    auth_level = Column(Integer, nullable=False)

    AUTH_LEVEL_NONE = 0
    AUTH_LEVEL_TRUSTED = 1
    AUTH_LEVEL_COORDINATOR = 2

    auth_level_names = {AUTH_LEVEL_NONE: '',
                        AUTH_LEVEL_TRUSTED: 'Trusted user',
                        AUTH_LEVEL_COORDINATOR:  'Coordinator'}

    user = relationship(Users, primaryjoin=(username == Users.username), foreign_keys=[username], uselist=False)
    language = relationship(Languages)

    @property
    def auth_level_name(self):
        return self.auth_level_names[self.auth_level]

    @property
    def is_trusted(self):
        return self.auth_level >= UserAuthority.AUTH_LEVEL_TRUSTED

    @property
    def is_coordinator(self):
        return self.auth_level >= UserAuthority.AUTH_LEVEL_COORDINATOR

    def __repr__(self):
        return '<UserAuthority %s:%s>' % (self.language_ref, self.auth_level)

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

    def __repr__(self):
        return '<PendingTranslation %s/%s %r owner=%r>' % (self.language_ref, self.description_id, self.short, self.owner_username)

    @classmethod
    def make_suggestion(self, description, language):
        """ From a description object and a language, make a suggestion for
        the description using existing parts, potentially using fuzzy matching """

        if description and language in description.translation:
            return description.translation[language].translation.partition("\n")[0], description.translation[language].translation.partition("\n")[2]
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

    @classmethod
    def make_quick_suggestion(self, description, language):
        """ From a description object and a language, make a quick suggestion for
        the description using existing parts, no fuzzy matching """

        if description and language in description.translation:
            return description.translation[language].translation.partition("\n")[0], description.translation[language].translation.partition("\n")[2]
        parts = description.get_description_part_objects()
        suggest = []
        for text, hash, part in parts:
            if part and language in part.translation:
                suggest.append(part.translation[language].part)
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

    @property
    def parts(self):
        return description_to_parts(self.short + "\n" + self.long)

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

    @property
    def age(self):
        return timesince(datetime.fromtimestamp(self.lastupdate),datetime.fromtimestamp(time.time()))

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

    # Accept translation. Note: does not check policy, that is the caller's responsibility.
    def accept_translation(self):
        """ Accepts translation by pushing it into the DDTP """
        session = Session.object_session(self)

        parts = self.description.get_description_part_objects()
        translated_parts = self.parts

        # First create translation object, updating existing if necessary
        if self.language_ref in self.description.translation:
            translation = self.description.translation[self.language_ref]
        else:
            translation = Translation(description_id=self.description_id, language=self.language_ref)
            session.add(translation)
        translation.translation = self.short + "\n" + self.long + "\n"

        # Then update the parts
        for text, hash, part in parts:
            # Create Part object if missing
            if part is None:
                part = PartDescription(description_id=self.description_id, part_md5=hash)
                session.add(part)
            # Can't use magic here, because the PartDescription object might
            # have just been created but the Part already exists.
            part_trans = session.query(Part).filter_by(part_md5=hash, language=self.language_ref).first()
            if not part_trans:
                part_trans = Part(part_md5=hash, language=self.language_ref)
                session.add(part_trans)
            part_trans.part = translated_parts.pop(0)

        # Add a message indicating acceptance
        message = "Translation Accepted\n" \
                  "Translators/Reviewers: %s\n" \
                  "Description: %s\n" \
                  "%s\n" % (", ".join([self.owner_username] + [r.username for r in self.reviews]),
                  self.short,
                  self.long)
        message = Messages(message=message,
                           language=self.language_ref,
                           for_description=self.description_id,
                           timestamp=int(time.time()))

        session.add(message)
        session.delete(self)
        for review in self.reviews:
            session.delete(review)

    def Get_flot_data(self):
        """ Returns all versions in a nice format """

        max_counter=100

        session = Session.object_session(self)

        values = list();
        Statistic2 = aliased(Statistic)
        values = session.query(Statistic2.value*1000/Statistic.value, Statistic.value, Statistic2.value). \
                filter(Statistic.stat == 'lang:pendingtranslation-'+self.language_ref). \
                filter(Statistic2.stat == 'lang:pendingreview-'+self.language_ref). \
                filter(Statistic.date == Statistic2.date). \
                order_by(Statistic.date.asc()). \
                limit(max_counter). \
                all()
        output_prozt = "var quote=%s;" % ([[i, stat[0]/10] for i, stat in enumerate(values)]) 
        output_total = "var trans=%s;" % ([[i, stat[1]] for i, stat in enumerate(values)])    
        output_trans = "var revie=%s;" % ([[i, stat[2]] for i, stat in enumerate(values)])

        return output_prozt+output_total+output_trans

class PendingTranslationReview(Base):
    """ A review of a translation """
    __tablename__ = 'pendingtranslationreview_tb'

    pending_translation_id = Column(Integer, ForeignKey('pendingtranslations_tb.pending_translation_id'), primary_key=True)
    username = Column(String, primary_key=True)

    user = relationship(Users, primaryjoin=(username == Users.username), foreign_keys=[username], uselist=False)
    translation = relationship(PendingTranslation, backref='reviews')

    def __repr__(self):
        return '<PendingTranslationReview %s/%s by %s>' % (self.translation.language_ref, self.translation.description_id, self.username)

    # In the future we might have different kinds of review, we could store
    # that data here

class Messages(Base):
    """ Messages, global, user or language """
    __tablename__ = 'messages_tb'

    message_id = Column(Integer, primary_key=True, autoincrement=True)

    # Specify who sees it:
    # all NULL: global
    # Language: for that language only
    # for_description and language: for the description and lang
    # User: for that user 
    # Both: Not allowed
    language = Column(String, ForeignKey('languages_tb.language'))
    for_description = Column(Integer, ForeignKey('description_tb.description_id'))
    to_user = Column(String, ForeignKey('users_tb.username'))

    from_user =  Column(String, ForeignKey('users_tb.username'))
    in_reply_to =  Column(Integer, ForeignKey('messages_tb.message_id'))
    timestamp = Column(Integer, nullable=False)
    message = Column(String, nullable=False)

    description = relationship("Description")
    parent = relation('Messages', remote_side=[message_id], backref="children")

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timestamp)

    def __repr__(self):
        return 'Messages(%s, message=%s, reply:%s)' % (self.message_id, self.message, str(self.in_reply_to))

    @classmethod
    def global_messages(cls, session):
        return session.query(cls) \
                          .filter(cls.to_user==None) \
                          .filter(cls.language==None) \
                          .filter(cls.for_description==None) \
                          .filter(cls.from_user!=None)

    @classmethod
    def team_messages(cls, session, language):
        return session.query(cls) \
                          .filter(cls.language==language) \
                          .filter(cls.for_description==None) \
                          .filter(cls.from_user!=None)

    @classmethod
    def user_messages(cls, session, username):
        return session.query(cls) \
                          .filter(cls.to_user==username) \
                          .filter(cls.from_user!=None)
