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

import os

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

TIME_ZONE = 'Europe/Amsterdam'

LANGUAGE_CODE = 'en-us'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media2')
STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = '/media/'
STATIC_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Code snipped from https://gist.github.com/ndarville/3452907
# Project secret-key-gen.py
try:
    SECRET_FILE = os.path.join(os.path.dirname(__file__), "secret.key")
    SECRET_KEY = open(SECRET_FILE).read().strip()
except IOError:
    try:
        import random
        SECRET_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
        secret = file(SECRET_FILE, 'w')
        secret.write(SECRET_KEY)
        secret.close()
    except IOError:
        Exception("Please create a %(SECRET_FILE)s file with random characters" \
                  " to generate your secret key!" % locals())


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_openid_consumer.middleware.OpenIDMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'ddtp.urls'


INSTALLED_APPS = (
    'django.contrib.sessions',
    'ddtp.ddtp_web',
    'ddtp.ddtss',
    'ddtp.database',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_openid_consumer',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), "sessions.db"),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-ddtp',
        'TIMEOUT': 4*3600,
    }
}

INTERNAL_IPS = ('127.0.0.1',)

DDTP_DATABASE=dict(drivername='postgresql',
                   database='ddtp')

# Optimistic lock timeout in seconds
DDTSS_LOCK_TIMEOUT=900
# If true, disables various permission checks
DEMO_MODE=False

# File to save all logging messages.
LOGFILE_NAME = '/var/log/ddtss/ddtss.log'
# 20 MegaByte.
LOGFILE_SIZE = 20 * 1024 * 1024
# Max 20 files.
LOGFILE_COUNT = 20
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s | %(levelname)s | Module[%(module)s] PID[%(process)d] Thread[%(thread)d] Message[%(message)s]'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': LOGFILE_NAME,
            'formatter': 'verbose',
            'maxBytes': LOGFILE_SIZE,
            'backupCount': LOGFILE_COUNT,
        }
    },
    'loggers': {
        # '' - Stands for get them all
        '': {
            'handlers': ['null', 'file'],
            'propagate': False,
            'level': 'DEBUG'
        }
    }
}
