# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import os
import re
from django.core.management.base import BaseCommand, CommandError

from django.core import management

class Command(BaseCommand):
    """ When we have direct access to a mirror, it is easier to simply let
    the user point to the mirror and specify distribution/component and let
    the script work it out. """

    help = "Imports packages files from a copy of a mirror"
    args = "path_to_mirror [dist/component ...]"

    requires_model_validation = False

    dist_comp_RE = re.compile(r'^[a-z-]+/[a-z-]+$')

    def handle(self, *args, **options):
        if not args:
            raise CommandError("Require a path to a mirror")
        path = args[0]
        tags = args[1:]

        # Validate path
        if not os.path.exists(path):
            raise CommandError("Given path %r does not exists" % path)
        if not os.path.exists(os.path.join(path,'dists')):
            raise CommandError("Given path %r does appear to be mirror, expected 'dists' directory" % path)

        for tag in tags:
            if not self.dist_comp_RE.match(tag):
                raise CommandError("Argument %r invalid, expect e.g. sid/main, wheezy/contrib, etc..." % tag)

            dist_path = os.path.join(path,'dists',tag)

            # Split out the distribution and component. If the distribution
            # is a symlink, extract the real name
            dist = tag.split('/')[0]

            if os.path.islink(os.path.join(path,'dists',dist)):
                dist = os.readlink(os.path.join(path,'dists',dist))

            args = [dist]

            # Looks for a english translation file
            trans_path = os.path.join(dist_path, 'i18n/Translation-en.bz2')
            if os.path.exists(trans_path):
                args.append(trans_path)

            # Process any binary architectures we find
            for arch in os.listdir(dist_path):
                if arch.startswith('binary-'):
                    package_path = os.path.join(dist_path, arch, 'Packages.bz2')
                    if os.path.exists(package_path):
                        args.append(package_path)

            self.stdout.write("Command: %s\n" % args)
            management.call_command('import_packages', *args)
