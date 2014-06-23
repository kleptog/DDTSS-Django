
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

# Use the generate_secret_key command to make the key
try:
    SECRET_KEY = open(os.path.join(os.path.dirname(__file__), "secret.key")).read()
except IOError:
    pass

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
