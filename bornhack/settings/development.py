from .base import *

# INSTALLED_APPS += ['debug_toolbar', ]

SECRET_KEY = 'bornhack_development'
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': local_dir('db.sqlite3'),
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
