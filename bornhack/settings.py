import os

import environ
env = environ.Env()
environ.Env.read_env()

def local_dir(entry):
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        entry
    )

WSGI_APPLICATION = 'bornhack.wsgi.application'
ROOT_URLCONF = 'bornhack.urls'

SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(',')

SITE_ID = 1

DATABASES = {
    'default': env.db(),
}

ADMINS = (
    ('bornhack sysadm', 'sysadm@bornhack.org'),
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'profiles',
    'camps',
    'shop',
    'news',
    'utils',
    'villages',
    'program',
    'info',

    'allauth',
    'allauth.account',
    'bootstrap3',
]

STATIC_URL = '/static/'
STATIC_ROOT = local_dir('static')
STATICFILES_DIRS = [local_dir('static_src')]
MEDIA_ROOT = env('MEDIA_ROOT')
LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TIME_ZONE')
#USE_I18N = True
#USE_L10N = True
USE_TZ = True
SHORT_DATE_FORMAT = 'd/m-Y'
DATE_FORMAT = 'd/m-Y'
DATETIME_FORMAT = 'd/m-Y H:i'
TIME_FORMAT = 'H:i'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [local_dir('templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.current_order',
                'shop.context_processors.user_has_tickets',
                'camps.context_processors.camp',
            ],
        },
    },
]


MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

LOGIN_REDIRECT_URL = 'profiles:detail'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Handles login to admin with username
    'allauth.account.auth_backends.AuthenticationBackend', # Handles regular logins
)

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[bornhack] '
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_REDIRECT_URL='/shop/'
LOGIN_URL = '/login/'

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

BOOTSTRAP3 = {
    'jquery_url': '/static/js/jquery.min.js',
    'javascript_url': '/static/js/bootstrap.min.js'
}

EPAY_MERCHANT_NUMBER = env('EPAY_MERCHANT_NUMBER')
EPAY_MD5_SECRET = env('EPAY_MD5_SECRET')

COINIFY_API_KEY = env('COINIFY_API_KEY')
COINIFY_API_SECRET = env('COINIFY_API_SECRET')
COINIFY_IPN_SECRET = env('COINIFY_IPN_SECRET')

LETTERHEAD_PDF_PATH = os.path.join(local_dir('static_src'), 'pdf', env('PDF_LETTERHEAD_FILENAME'))
PDF_ARCHIVE_PATH='/usr/local/www/pdf_archive/'

BANKACCOUNT_IBAN = env('BANKACCOUNT_IBAN')
BANKACCOUNT_SWIFTBIC = env('BANKACCOUNT_SWIFTBIC')
BANKACCOUNT_REG = env('BANKACCOUNT_REG')
BANKACCOUNT_ACCOUNT = env('BANKACCOUNT_ACCOUNT')

TICKET_CATEGORY_ID = env('TICKET_CATEGORY_ID')

DEBUG = env('DEBUG')
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    INSTALLED_APPS += ['debug_toolbar', ]
    MIDDLEWARE_CLASSES += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]

else:
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_PORT = env('EMAIL_PORT')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = env('EMAIL_USE_TLS')
    DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
    SERVER_EMAIL = env('DEFAULT_FROM_EMAIL')
    ARCHIVE_EMAIL = env('ARCHIVE_EMAIL')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# schedule settings
SCHEDULE_MIDNIGHT_OFFSET_HOURS=int(env('SCHEDULE_MIDNIGHT_OFFSET_HOURS'))
SCHEDULE_TIMESLOT_LENGTH_MINUTES=int(env('SCHEDULE_TIMESLOT_LENGTH_MINUTES'))

