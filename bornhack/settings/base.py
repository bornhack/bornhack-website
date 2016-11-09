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

    'allauth',
    'allauth.account',
    'bootstrap3',
]

STATIC_URL = '/static/'
STATIC_ROOT = local_dir('static')
STATICFILES_DIRS = [local_dir('static_src')]
MEDIA_ROOT = env('MEDIA_ROOT')
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
                'camps.context_processors.current_camp',
                'shop.context_processors.current_order',
                'shop.context_processors.user_has_tickets',
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
