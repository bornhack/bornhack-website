from .base import *

# INSTALLED_APPS += ['debug_toolbar', ]

SECRET_KEY = 'bornhack_development'
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bornhack_dev',
        'USER': 'bornhack',
        'PASSWORD': 'bornhack',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
