import os
from .environment_settings import *

def local_dir(entry):
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        entry
    )

DJANGO_BASE_PATH = os.path.dirname(os.path.dirname(__file__))

WSGI_APPLICATION = 'bornhack.wsgi.application'
ROOT_URLCONF = 'bornhack.urls'


SITE_ID = 1

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

    'channels',

    'profiles',
    'camps',
    'shop',
    'news',
    'utils',
    'villages',
    'program',
    'info',
    'sponsors',
    'ircbot',
    'teams',
    'people',
    'tickets',
    'bar',
    'backoffice',

    'allauth',
    'allauth.account',
    'bootstrap3',
    'django_extensions',
]

#MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATIC_ROOT = local_dir('static')
STATICFILES_DIRS = [local_dir('static_src')]
LANGUAGE_CODE = 'en-us'
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
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.current_order',
                'camps.context_processors.camp',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Handles login to admin with username
    'allauth.account.auth_backends.AuthenticationBackend', # Handles regular logins
)

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[bornhack] '
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_REDIRECT_URL='/'
LOGIN_URL = '/login/'

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

BOOTSTRAP3 = {
    'jquery_url': '/static/js/jquery.min.js',
    'javascript_url': '/static/js/bootstrap.min.js'
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    INSTALLED_APPS += [
        'debug_toolbar',
    ]
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = "127.0.0.1"
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
else:
    SESSION_COOKIE_SECURE=True
    CSRF_COOKIE_SECURE=True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'syslog': {
            'format': '%(levelname)s %(name)s.%(funcName)s(): %(message)s'
        },
        'console': {
            'format': '[%(asctime)s] %(name)s.%(funcName)s() %(levelname)s %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
    },
    'loggers': {
        # send the bornhack logger to console at DEBUG level,
        # do not propagate bornhack.* messages up to the root logger
        'bornhack': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


