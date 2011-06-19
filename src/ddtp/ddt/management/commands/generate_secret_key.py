# DDTSS-Django - A Django implementation of the DDTP/DDTSS website    
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>    
# See LICENCE file for details.

import os

from random import choice
from django.conf import settings
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = "Generates a new SECRET_KEY."

    requires_model_validation = False
    can_import_settings = False

    def handle_noargs(self, **options):
        from ddtp.settings import __file__ as settings_file
        key_file = os.path.join(os.path.dirname(settings_file), "secret.key")
        if os.path.exists(key_file):
            print "Keyfile %r already exists" % key_file
        else:
            key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            open(key_file,"w").write(key)
            print "Keyfile %r created with key" % key_file
