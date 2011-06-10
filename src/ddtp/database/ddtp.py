import hashlib
from .db import Base, get_db_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy import Table, Column, Integer, String, Date, MetaData, ForeignKey

class DescriptionTag(Base):
    __tablename__ = 'description_tag_tb'

    description_tag_id = Column(Integer, primary_key=True)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)
    tag = Column(String)
    date_begin = Column(Date)
    date_end = Column(Date)

    def __repr__(self):
        return 'DescriptionTag(%d, descr=%d, tag=%r, %s-%s)' % (self.description_tag_id, self.description_id, self.tag, self.date_begin.strftime("%Y-%m-%d"), self.date_end.strftime("%Y-%m-%d"))

class ActiveDescription(Base):
    __tablename__ = 'active_tb'

    description_id = Column(Integer, ForeignKey('description_tb.description_id'), primary_key=True)

    def __repr__(self):
        return 'ActiveDescription(%d)' % self.description_id

class Description(Base):
    __tablename__ = 'description_tb'

    description_id = Column(Integer, primary_key=True)
    description_md5 = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    prioritize = Column(Integer, nullable=False)
    package = Column(String, nullable=False)
    source = Column(String, nullable=False)

    owners = relationship('Owner', backref='description')
    package_versions = relationship('PackageVersion', backref='description')
    translations = relationship('Translation', backref='description')
    tags = relationship('DescriptionTag', backref='description')
    parts = relationship('PartDescription', backref='description')

    def translation(self, lang):
        """ Returns the translation for this description for a given language, or None of not found """
        return Session.object_session(self).query(Translation).filter_by(description_id=self.description_id).filter_by(language=lang).first()

    def get_description_parts(self):
        """ Returns a list of (string, md5) which are the parts of this description """
        lines = self.description.split('\n')
        parts = [lines.pop(0)]  # Take header as is
        s = ""
        for line in lines:
            if line and line != " .":
                s += line + "\n"
            else:
                if s: parts.append(s)
                s = ""
        if s: parts.append(s)
        return [(p, hashlib.md5(p).hexdigest()) for p in parts]

    def get_description_part_objects(self):
        """ Returns a list of (string, md5, partobj) for the parts of this
        description.
        
        Note this calculates the parts, you can use the 'parts' property to
        get the parts in the database """
        parts = self.get_description_parts()
        
        return [(p[0], p[1], Session.object_session(self).query(PartDescription).filter_by(part_md5=p[1]).first()) for p in parts]

    def __repr__(self):
        return 'Description(%d, package=%r, source=%r)' % (self.description_id, self.package, self.source)

class Owner(Base):
    __tablename__ = 'owner_tb'

    owner_id = Column(Integer, primary_key=True)
    owner = Column(String, nullable=False)
    language = Column(String, nullable=False)
    lastsend = Column(Date, nullable=False)
    lastseen = Column(Date, nullable=False)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)

    def __repr__(self):
        return 'Owner(%d, owner=%r, lang=%r, descr=%d)' % (self.owner_id, self.owner, self.language, self.description_id)

class PackageVersion(Base):
    __tablename__ = 'package_version_tb'

    package_version_id = Column(Integer, primary_key=True)
    package = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)

    def __repr__(self):
        return 'PackageVersion(%d, package=%s (%s), descr=%d)' % (self.package_version_id, self.package, self.version, self.description_id)

class Packages(Base):
    __tablename__ = 'packages_tb'

    packages_id = Column(Integer, primary_key=True)
    package = Column(String, nullable=False)
    source = Column(String, nullable=False)
    version = Column(String, nullable=False)
    tag = Column(String)
    priority = Column(String, nullable=False)
    maintainer = Column(String, nullable=False)
    task = Column(String)
    section = Column(String, nullable=False)
    description = Column(String, nullable=False)
    description_md5 = Column(String, nullable=False)

    def __repr__(self):
        return 'Packages(%d, package=%r, source=%r, version=%r)' % (self.packages_id, self.package, self.source, self.version)

class PartDescription(Base):
    __tablename__ = 'part_description_tb'

    part_description_id = Column(Integer, primary_key=True)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)
    part_md5 = Column(String, nullable=False)

    def translation(self, lang):
        """ Returns the translation for this part for a given language, or None of not found """
        return Session.object_session(self).query(Part).filter_by(part_md5=self.part_md5).filter_by(language=lang).first()

    def __repr__(self):
        return 'PartDescription(%d, descr=%d, %s)' % (self.part_description_id, self.description_id, self.part_md5)

class Part(Base):
    """ Translated parts """
    __tablename__ = 'part_tb'

    part_id = Column(Integer, primary_key=True)
    part_md5 = Column(String, nullable=False)
    part = Column(String, nullable=False)
    language = Column(String, nullable=False)

    def __repr__(self):
        return 'Part(%d, %s, lang=%s)' % (self.part_id, self.part_md5, self.language)

# ppart?
class Suggestion(Base):
    __tablename__ = 'suggestion_tb'

    suggestion_id = Column(Integer, primary_key=True)
    package = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description_md5 = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    language = Column(String, nullable=False)
    importer = Column(String, nullable=False)
    importtime = Column(Date, nullable=False)

class Translation(Base):
    __tablename__ = 'translation_tb'

    translation_id = Column(Integer, primary_key=True)
    translation = Column(String, nullable=False)
    language = Column(String, nullable=False)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)

    def __repr__(self):
        return 'Translation(%d, descr=%d, lang=%s)' % (self.translation_id, self.description_id, self.language)

class Version(Base):
    __tablename__ = 'version_tb'

    version_id = Column(Integer, primary_key=True)
    version = Column(String, nullable=False)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)

    def __repr__(self):
        return 'Version(%d, desc=%d, version=%s)' % (self.version_id, self.description_id, self.version)