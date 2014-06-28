# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import re
import hashlib
import subprocess

from collections import defaultdict
from datetime import date
from debian.deb822 import Deb822
from ddtp.database import db, ddtp, ddtss
from django.core.management.base import BaseCommand, CommandError
from ddtp.ddtss.translationmodel import DefaultTranslationModel

class Command(BaseCommand):
    help = "Imports a wordlist file into the database"
    args = "lang wordsfile"

    requires_model_validation = False

    comma_sep_RE = re.compile(r'\s*,\s*')

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("Require a language and a filename.")
        language = args[0]
        filename = args[1]

        self.session = db.get_db_session()
        self.session.bind.echo=False

        self.lang = self.session.query(ddtss.Languages).get(language)
        if not self.lang:
            raise CommandError("Unknown language '%s'" % language)

        file = open(filename)
        words = set()

        for line in file:
            line = line.strip()
            if not line:
                continue

            word, text = line.split('\t', 1)

            word = word.lower()

            if word in words:
                print "Skipping duplicate '%s'" % word
                continue

            words.add(word)

            newword = ddtss.WordlistEntry(language=self.lang, word=word, translation=text)

            self.session.add(newword)

        self.session.commit()
