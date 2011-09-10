# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import os
import re
import time
import hashlib
from collections import defaultdict

from random import choice
from django.conf import settings
from django.core.management.base import NoArgsCommand

from ddtp.database import db, ddtp, ddtss
from sqlalchemy import Table, Column, Integer, String, Date, LargeBinary, MetaData, ForeignKey
from ddtp.ddtss.translationmodel import DefaultTranslationModel

class DDTSS(db.Base):
    __tablename__ = 'ddtss'

    key = Column(String, primary_key=True)
    value = Column(LargeBinary, nullable=False)

# Language names:
lang_names = {
    'da': 'Danish',
    'de': 'German',
    'ca': 'Catalan',
    'cs': 'Czech',
    'fr': 'French',
    'hu': 'Hungarian',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'nl': 'Dutch',
    'pl': 'Polish',
    'pt_BR': 'Brazilian Portuguese',
    'pt': 'Portugese',
    'ru': 'Russian',
    'sk': 'Slovak',
    'sv': 'Swedish',
    'uk': 'Ukrainian',
    'es': 'Spanish',
    'eo': 'Esperanto',
    'fi': 'Finnish',
    'zh_CN': 'Simplified Chinese',
    'zh_TW': 'Traditional Chinese',
    'km_KH': 'Cambodian (Khmer)',
}

users = None
languages = None
packages = None
package_reviews = None

ignore = lambda x, y: None

def handle_langs(a,b):
    langs = b[0].split(',')

    for lang in languages:
        lang.enabled_ddtss = (lang.language in langs)
        lang.fullname = lang_names.get(lang.language,'')
        lang.translationmodel = DefaultTranslationModel()

def handle_package_state(a,b):
    state = b[0].split(',')
    if state[0] == 'untranslated':
        packages[(a[0],a[1])].state = ddtss.PendingTranslation.STATE_PENDING_TRANSLATION
    elif state[0] == 'forreview':
        packages[(a[0],a[1])].state = ddtss.PendingTranslation.STATE_PENDING_REVIEW
    else:
        print "Unknown state %r" % b[0]

keymap = (
   (r'^aliases/([\w.]+)$', r'^([\w.@+-]+)$', lambda a,b: setattr(users[a[0]],'email',b[0])),
   (r'^aliases/([\w.]+)/(counttranslations|countreviews)$', r'^(\d+)$', lambda a,b: setattr(users[a[0]], a[1], b[0])),
   (r'^aliases/([\w.]+)/(key|md5password|realname)$', r'^(.*)$', lambda a,b: setattr(users[a[0]], a[1], b[0])),
   (r'^aliases/([\w.]+)/(lastlanguage)$', r'^(.*)$', lambda a,b: setattr(users[a[0]], 'lastlanguage_ref', b[0])),
   (r'^aliases/([\w.]+)/timestamp$', r'^(\d+)$', lambda a,b: setattr(users[a[0]], 'lastseen', int(b[0]))),
   (r'^aliases/([\w.]+)/(active|password)$', r'', ignore),
   (r'^aliases/([\w.]+)/isadmin$', r'', ignore),  # TODO
   (r'^aliases/([\w.]+)/messages$', r'', ignore),  # TODO
   (r'^(\w+)/config/numreviewers$', r'^(\d+)$', lambda a,b: languages[a[0]].translation_model.set_threshold(int(b[0]))),
   (r'^(\w+)/config/requirelogin$', r'^(\d+)$', lambda a,b: languages[a[0]].translation_model.set_login_required(int(b[0]))),
   (r'^(\w+)/config/minuntranslated$', r'', ignore),
   (r'^(\w+)/done/', r'', ignore),
   (r'^(\w+)/logs/', r'', ignore),
   (r'^(\w+)/packages/([\w.+-]+)$', r'^(.*)$', handle_package_state),
   (r'^(\w+)/packages/([\w.+-]+)/age$', r'(?sm)^(.*)$', lambda a,b: setattr(packages[(a[0],a[1])], 'agefield', b[0])),
   (r'^(\w+)/packages/([\w.+-]+)/(\w+)$', r'(?sm)^(.*)$', lambda a,b: setattr(packages[(a[0],a[1])], a[2], b[0])),
   (r'^(\w+)/messages$', r'', ignore),
   (r'^descrmatch/', r'^(.*)$', ignore),
   (r'^todo/', r'', ignore),
   (r'^lock/', r'^(.*)$', ignore),
   (r'^\w+/scores$', r'^(.*)$', ignore),
   (r'^suggestion/', r'', ignore),
   (r'^users/([\w.@+-]+)$', r'^([\w.]+)$', lambda a,b: setattr(users[b[0]], 'email', a[0])),  # Alternate email
   (r'^messages', r'^(.*)$', ignore),  #TODO
   (r'^config/', r'^(.*)$', ignore),
   (r'^lang(/disabled)?', r'^(.*)$', ignore),

)

class Command(NoArgsCommand):
    help = "Generates a new SECRET_KEY."

    requires_model_validation = False
    can_import_settings = False

    def handle_noargs(self, **options):

        global users, languages, packages, package_reviews

        session = db.get_db_session()

        users = defaultdict(ddtss.Users)
        packages = defaultdict(ddtss.PendingTranslation)

        res = session.query(ddtss.Languages).all()
        languages = defaultdict( lambda: ddtss.Languages(translation_model=DefaultTranslationModel()), ((r.language, r) for r in res) )

        for key, val in session.query(DDTSS.key, DDTSS.value).yield_per(100):
            for key_regex, val_regex, func in keymap:
                key_match = re.match(key_regex, key)
                if key_match:
                    val_match = re.match(val_regex, val)
                    if not val_match:
                        print "Key %r value doesn't match regex" % key
                        break
                    func(key_match.groups(), val_match.groups())
                    break
            else:
                print "Unknown key: %r" % key

        print "%d users total" % len(users)

        now = time.time()
        save_users = []
        for username, user in users.iteritems():
            if not user.key:
                continue
            if user.lastseen < now-(180*86400):
                continue
            if user.lastlanguage_ref and user.lastlanguage_ref != 'xx':
                user.lastlanguage = languages[user.lastlanguage_ref]
            else:
                user.lastlanguage_ref = None
            user.active = True
            user.username = username
            save_users.append(user)

        print "%d users saved" % len(save_users)

        print "%d packages total" % len(packages)

        save_package = []
        for package_key, package in packages.iteritems():
          try:
            if not hasattr(package,'data'):  # Incomplete record
                continue
            if package.state is None:
                continue

            if not hasattr(package, 'long'):  # Not submitted even once
                print "%r skipped due to not used" % (package_key,)
                continue

            # The old system didn't know the description ID, so we look it
            # up by the MD5 sum of the description in the data field
            m = re.search(r'(?m)^Description: (.*)\n((?: .*\n)+)', package.data)
            if not m:
                print "Couldn't extract description from %r" % package_key
                continue
            short, long = m.groups()
            md5 = hashlib.md5(short+"\n"+long).hexdigest()

            descr, = session.query(ddtp.Description.description_id).filter_by(description_md5=md5).one()
            package.description_id = descr

            # Handle renamed fields
            if hasattr(package, 'iter'):
                package.iteration = package.iter
            else:
                package.iteration = 0
            if hasattr(package, 'owner'):
                package.owner_username = package.owner
            if hasattr(package, 'timestamp'):
                package.lastupdate = package.timestamp
            else:
                package.lastupdate = now

            if hasattr(package,'agefield'):
                package.firstupdate = package.agefield
            else:
                package.firstupdate = now
            package.language = languages[package_key[0]]

            save_package.append(package_key)
          except Exception, e:
            print "Package %r: %s" % (package_key, e)

        print "%d packages saved" % len(save_package)

        # Update languages
        for lang in languages:
            languages[lang].language = lang
            languages[lang].milestone_high = "rtrn:" + lang
            languages[lang].milestone_medium = "part:1-" + lang
            languages[lang].milestone_low = "popc:sid-500"
            if languages[lang].fullname is None:
                languages[lang].fullname = lang_names.get(languages[lang].language,'')
        session.add_all(languages.values())

        # Update users
        session.add_all(save_users)

        # Update packages
        session.add_all( (packages[p] for p in save_package) )

        # Now we can do the reviews
        for package_key in save_package:
          try:
            package = packages[package_key]
            if not hasattr(package, 'reviewers'):
                continue
            for reviewer in package.reviewers.split(','):
                review = ddtss.PendingTranslationReview()
                review.translation = package
                review.username = reviewer
                session.add(review)
          except Exception, e:
            print "Package %r: %s" % (package_key, e)

        session.commit()
        print "Done."
