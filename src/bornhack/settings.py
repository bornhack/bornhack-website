from pathlib import Path

from .environment_settings import *  # noqa: F403
from utils import range_fields  # noqa: F401

# monkeypatch postgres Range object to support lookups

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# TODO: remove this and update references to DJANGO_BASE_PATH to use BASE_DIR
DJANGO_BASE_PATH = BASE_DIR

WSGI_APPLICATION = "bornhack.wsgi.application"
ASGI_APPLICATION = "bornhack.routing.application"
ROOT_URLCONF = "bornhack.urls"

ACCOUNT_ADAPTER = "allauth_2fa.adapter.OTPAdapter"

SITE_ID = 1

ADMINS = (("bornhack sysadm", "sysadm@bornhack.org"),)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.gis",
    "channels",
    "corsheaders",
    "profiles",
    "camps",
    "shop",
    "news",
    "utils",
    "villages",
    "program",
    "info",
    "sponsors",
    "ircbot",
    "teams",
    "people",
    "tickets",
    "bar",
    "backoffice",
    "events",
    "rideshare",
    "tokens",
    "feedback",
    "economy",
    "wishlist",
    "facilities",
    "phonebook",
    "maps",
    "allauth",
    "allauth.account",
    "allauth_2fa",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "bootstrap3",
    "django_extensions",
    "reversion",
    "leaflet",
    "oauth2_provider",
    "taggit",
]

# MEDIA_URL = '/media/'
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static_src"]
LANGUAGE_CODE = "en-us"
# USE_I18N = True
# USE_L10N = True
USE_TZ = True
SHORT_DATE_FORMAT = "Ymd"
DATE_FORMAT = "l, M jS, Y"
DATETIME_FORMAT = "l, M jS, Y, H:i (e)"
TIME_FORMAT = "H:i"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.current_order",
                "camps.context_processors.camp",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",  # Handles login to admin with username
    "allauth.account.auth_backends.AuthenticationBackend",  # Handles regular logins
)

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[bornhack] "
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

BOOTSTRAP3 = {
    "jquery_url": "/static/js/jquery-3.3.1.min.js",
    "javascript_url": "/static/js/bootstrap.min.js",
}
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "utils.middleware.RedirectExceptionMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/api/*$"

if DEBUG:  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
    INTERNAL_IPS = "127.0.0.1"
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ]
else:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "syslog": {"format": "%(levelname)s %(name)s.%(funcName)s(): %(message)s"},
        "console": {
            "format": "[%(asctime)s] %(name)s.%(funcName)s() %(levelname)s %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        # send the bornhack logger to console at DEBUG level,
        # do not propagate bornhack.* messages up to the root logger
        "bornhack": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

GRAPHENE = {"SCHEMA": "bornhack.schema.schema"}
LEAFLET_CONFIG = {
    "PLUGINS": {"forms": {"auto-include": True}},
}

# used to find the economy team
ECONOMY_TEAM_NAME = "Economy"

# we have some large formsets sometimes
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000

# use captcha form
ACCOUNT_SIGNUP_FORM_CLASS = "bornhack.forms.AllAuthSignupCaptchaForm"

# django 3.2 https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

WKHTMLTOPDF_CMD_OPTIONS = {
    "quiet": True,
    "enable-local-file-access": True,
}

OAUTH2_PROVIDER = {
    "SCOPES": {
        "profile:read": "Profile read scope",
        "phonebook:read": "Phonebook read scope",
    },
}
