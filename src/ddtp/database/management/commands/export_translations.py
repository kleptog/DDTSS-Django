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

from datetime import date, timedelta
from debian.deb822 import Deb822
from ddtp.database import db, ddtp
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Exports the translation file for a language"
    args = "lang tag filename"

    requires_model_validation = False

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("Requires a language, a tag and an output filename")
        lang = args[0]
        tag = args[1]
        filename = args[2]

        f = open(filename, "w")

        session = db.get_db_session()
        session.bind.echo=False

        output = False
        for trans, descr, descr_tag in session.query(ddtp.Translation, ddtp.Description, ddtp.DescriptionTag). \
                                          filter(ddtp.Translation.description_id == ddtp.Description.description_id). \
                                          filter(ddtp.Description.description_id == ddtp.DescriptionTag.description_id). \
                                          filter(ddtp.Translation.language == lang). \
                                          filter(ddtp.DescriptionTag.date_end >= date.today()-timedelta(days=7)). \
                                          filter(ddtp.DescriptionTag.tag == tag). \
                                          order_by(ddtp.Description.package). \
                                          yield_per(100):
            trans_para = Deb822()
            trans_para['Package'] = descr.package
            trans_para['Description-md5'] = descr.description_md5
            trans_para['Description-%s' % lang] = trans.translation
            
            # Minor nagic here: the translation has an extra newline here,
            # which we use to seperate the paragraphs
            f.write(trans_para.dump().encode('utf-8'))
            output = True

        if not output:
            self.stderr.write("WARNING: No output for tag %r, language %r\n" % (tag, lang))
