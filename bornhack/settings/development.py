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
LETTERHEAD_PDF_PATH = os.path.join(local_dir('static_src'), 'pdf', 'bornhack_2016_test_letterhead.pdf')
COINIFY_API_KEY = '{{ coinify_api_key }}'
COINIFY_API_SECRET = '{{ coinify_api_secret }}'
