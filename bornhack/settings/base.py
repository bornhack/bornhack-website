import os


def local_dir(entry):
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        entry
    )

WSGI_APPLICATION = 'bornhack.wsgi.application'
ROOT_URLCONF = 'bornhack.urls'

SITE_ID = 1

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
    'tickets',

    'allauth',
    'allauth.account',
    'bootstrap3',
]

STATIC_URL = '/static/'
STATIC_ROOT = local_dir('static')
STATICFILES_DIRS = [local_dir('static_src')]
MEDIA_URL = '/media/'
MEDIA_ROOT = local_dir('media')

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

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
    'django.contrib.auth.backends.ModelBackend',  # Login to admin with username
    'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[bornhack] '
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_URL = '/login/'

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
