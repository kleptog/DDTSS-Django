# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import hashlib
from .db import Base, with_db_session
from sqlalchemy.orm import relationship, collections, aliased
from sqlalchemy.orm.session import Session
from sqlalchemy import Table, Column, Integer, String, Date, MetaData, ForeignKey

class DescriptionTag(Base):
    """ Records for each description which releases it was in """
    __tablename__ = 'description_tag_tb'

    description_tag_id = Column(Integer, primary_key=True)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)
    tag = Column(String)
    date_begin = Column(Date)
    date_end = Column(Date)

    def __repr__(self):
        return 'DescriptionTag(%d, descr=%d, tag=%r, %s-%s)' % (self.description_tag_id, self.description_id, self.tag, self.date_begin.strftime("%Y-%m-%d"), self.date_end.strftime("%Y-%m-%d"))

class ActiveDescription(Base):
    """ Record is present of description is active """
    __tablename__ = 'active_tb'

    description_id = Column(Integer, ForeignKey('description_tb.description_id'), primary_key=True)

    def __repr__(self):
        return 'ActiveDescription(%d)' % self.description_id

class Description(Base):
    """ Main description table. Note that a majority of the fields in this
    table aren't as useful as they appear.  This represents unique
    descriptions.  The fields prioritize, package, source are for *some*
    package with this description """

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

    # Provides access to translations, as a dict
    translation = relationship('Translation', collection_class=collections.attribute_mapped_collection('language'))

    def short(self):
        """ Returns the title of the description """
        return self.description.partition("\n")[0]
    def long(self):
        """ Returns the body of the description """
        return self.description.partition("\n")[2]

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
        return [(p, hashlib.md5(p.encode('utf-8')).hexdigest()) for p in parts]

    def get_description_part_objects(self):
        """ Returns a list of (string, md5, partobj) for the parts of this
        description.

        Note this calculates the parts, you can use the 'parts' property to
        get the parts in the database """
        parts = self.get_description_parts()

        return [(p[0], p[1], Session.object_session(self).query(PartDescription).filter_by(part_md5=p[1]).first()) for p in parts]

    def get_potential_fuzzy_matches(self, lang):
        """ Returns a list of pairs (text,Parts) which may be fuzzy matches
        for this description.  The part is the already translated version,
        included because we needed to look it up anyway for existence """

        session = Session.object_session(self)
        # Find all descriptions which share a part with this description
        PartDescr2=aliased(PartDescription)
        related_descrs = set( d for d, in session.query(PartDescr2.description_id).
                                                  join(PartDescription, PartDescription.part_md5==PartDescr2.part_md5).
                                                  filter(PartDescription.description_id==self.description_id))
        # Always add self, as part_description table is not complete
        related_descrs.add(self.description_id)

        # Finally, find all parts of all descriptions which have been
        # translated and and part of a package which share a source or
        # package
        Descr2 = aliased(Description)
        related_parts = session.query(Part, Descr2).join(PartDescription, PartDescription.part_md5 == Part.part_md5). \
                                                    join(Descr2, Descr2.description_id == PartDescription.description_id). \
                                                    join(Description, (Description.package == Descr2.package) | (Description.source == Descr2.source)). \
                                                    filter(Description.description_id.in_(related_descrs)). \
                                                    filter(Part.language == lang).all()

        # First we go through the descriptions, deconstructing them into parts
        descr_map = dict( (part_md5, part) for _, descr in related_parts for part, part_md5 in descr.get_description_parts() )

        result = [ (descr_map.get(trans.part_md5), trans) for trans, _ in related_parts ]

        return result

    def __repr__(self):
        return 'Description(%d, package=%r, source=%r)' % (self.description_id, self.package, self.source)

class Owner(Base):
    """ This table is for tracking owner's, that is, who the description was
    emailed to to translate.  Only used by the email interface.  """

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
    """ Tracks which versions of each package use which description """

    __tablename__ = 'package_version_tb'

    package_version_id = Column(Integer, primary_key=True)
    package = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)

    def __repr__(self):
        return 'PackageVersion(%d, package=%s (%s), descr=%d)' % (self.package_version_id, self.package, self.version, self.description_id)

class Packages(Base):
    """ List of packages. Not quite sure what the purpose of this is that
    isn't covered by PackageVersions.  """
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
    """ Untranslated parts. The actual string comes from the Description table """

    __tablename__ = 'part_description_tb'

    part_description_id = Column(Integer, primary_key=True)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)
    part_md5 = Column(String, nullable=False)

    def translations(self):
        """ Returns a dict of translations for with part, indexed by language """
        return dict( Session.object_session(self).query(Part.language, Part).filter_by(part_md5=self.part_md5).all() )

    # Provides access to translations, as a dict
    translation = relationship('Part', collection_class=collections.attribute_mapped_collection('language'))

    @property
    def other_descriptions(self):
        """ Return the other PartDescriptions with the same md5. So same part in other descriptions """
        return Session.object_session(self).query(PartDescription).filter_by(part_md5=self.part_md5).all()

    def __repr__(self):
        return 'PartDescription(%d, descr=%d, %s)' % (self.part_description_id, self.description_id, self.part_md5)

class Part(Base):
    """ Translated parts """
    __tablename__ = 'part_tb'

    part_id = Column(Integer, primary_key=True)
    part_md5 = Column(String, ForeignKey('part_description_tb.part_md5'), nullable=False)
    part = Column(String, nullable=False)
    language = Column(String, nullable=False)

    def __repr__(self):
        return 'Part(%d, %s, lang=%s)' % (self.part_id, self.part_md5, self.language)

# There is a ppart table but it has never been used.

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
    """ Stores translated descriptions, parts are in Part table. """
    __tablename__ = 'translation_tb'

    translation_id = Column(Integer, primary_key=True)
    translation = Column(String, nullable=False)
    language = Column(String, nullable=False)
    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)

    def __repr__(self):
        return 'Translation(%d, descr=%d, lang=%s)' % (self.translation_id, self.description_id, self.language)

# This table is old, back from the time when it was assumed that
# descriptions only belonged to one package.  It has been superseded by the
# packages_versions table.
#
#class Version(Base):
#    __tablename__ = 'version_tb'
#
#    version_id = Column(Integer, primary_key=True)
#    version = Column(String, nullable=False)
#    description_id = Column(Integer, ForeignKey('description_tb.description_id'), nullable=False)
#
#    def __repr__(self):
#        return 'Version(%d, desc=%d, version=%s)' % (self.version_id, self.description_id, self.version)
