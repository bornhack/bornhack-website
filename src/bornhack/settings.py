from pathlib import Path

from .environment_settings import *  # noqa: F403
from utils import range_fields  # noqa: F401

# range_fields monkeypatches postgres Range object to support lookups

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

WSGI_APPLICATION = "bornhack.wsgi.application"
ASGI_APPLICATION = "bornhack.routing.application"
ROOT_URLCONF = "bornhack.urls"

ACCOUNT_ADAPTER = "bornhack.allauth.UsernameUUIDAdapter"

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
    "django.contrib.humanize",
    "colorfield",
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
    "allauth.socialaccount",
    "allauth.mfa",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "django_bootstrap5",
    "django_extensions",
    "reversion",
    "leaflet",
    "oauth2_provider",
    "taggit",
    "django_tables2",
    "django_filters",
]

# MEDIA_URL = '/media/'
STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "static")
STATICFILES_DIRS = [BASE_DIR / "static_src"]
LANGUAGE_CODE = "en-us"

FORMAT_MODULE_PATH = [
    "bornhack.formats",
]

USE_TZ = True

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
                "utils.context_processors.is_volunteer",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",  # Handles login to admin with username
    "allauth.account.auth_backends.AuthenticationBackend",  # Handles regular logins
)

MFA_SUPPORTED_TYPES = [
    "webauthn",
    "totp",
    "recovery_codes",
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[bornhack] "
ACCOUNT_SIGNUP_FORM_HONEYPOT_FIELD = "gender"
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

# include captcha field in signup form
ACCOUNT_FORMS = {"signup": "bornhack.forms.AllAuthSignupCaptchaForm"}
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "utils.middleware.RedirectExceptionMiddleware",
    "camps.middleware.RequestCampMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "oauth2_provider.middleware.OAuth2ExtraTokenMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/profile/api/$|^/o/.*$|^/bornhack-20[0-9]{2}/phonebook/json/$"

if DEBUG_TOOLBAR_ENABLED:  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
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

if not DEBUG:  # noqa: F405
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
    "DEFAULT_CENTER": (55.38723, 9.94080),
    "DEFAULT_ZOOM": 17,
    "PLUGINS": {"forms": {"auto-include": True}},
}

# used to find the economy team
ECONOMY_TEAM_NAME = "Economy"

# we have some large formsets sometimes
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000

# django 3.2 https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    "OIDC_RSA_PRIVATE_KEY": OIDC_RSA_PRIVATE_KEY,  # noqa: F405
    "SCOPES": {
        # required
        "openid": "OpenID Connect scope",
        # deprecated api scope, remove after 2025 camp
        "profile:read": "Allow the remote site to read your bornhack.dk username (uuid), user id, profile public credit name, profile description, and a list of team memberships using the profile API endpoint (scope profile:read). NOTE: This scope is being deprecated soon! Ask the BornHack website team for more info.",
        # standard OIDC claim scopes
        "profile": "Allow the remote site to read your profile public_credit_name, description, and update time (scope: profile)",
        "email": "Allow the remote site to read your email address (scope: email)",
        "address": "Allow the remote site to read your profile location (scope: address)",
        "phone": "Allow the remote site to read your profile phonenumber (scope: phone)",
        # custom bornhack user claim scopes
        "groups:read": "Allow the remote site to read a list of your group memberships (scope: groups:read).",
        "location:read": "Allow the remote site to read your profile location (scope: location:read)",
        "location:write": "Allow the remote site to write your profile location (scope: location:write)",
        "permissions:read": "Allow the remote site to read a list of your assigned permissions (scope: permissions:read).",
        "teams:read": "Allow the remote site to read a list of your team memberships and team lead status (scope: teams:read)",
        # api scopes
        "phonebook:admin": "Allow the remote site to read the camp phonebook, including service numbers and unlisted numbers. Also allow the remote site to use to the POC API. This scope is only relevant for POC team leads (scope: phonebook:admin).",
        "phonebook:read": "Allow the remote site to read the camp phonebook (scope: phonebook:read).",
    },
    "PKCE_REQUIRED": True,
    "OAUTH2_VALIDATOR_CLASS": "bornhack.oauth_validators.BornhackOAuth2Validator",
}

# only used for bootstrap-devsite
UPCOMING_CAMP_YEAR = 2025

# django-tables2 settings
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5-responsive.html"
DJANGO_TABLES2_TABLE_ATTRS = {
    "class": "table table-hover table-striped",
}

# fallback settings for views/pages/places where l10n is disabled
DATE_FORMAT = "l, M jS, Y"
DATETIME_FORMAT = "l, M jS, Y, H:i (e)"
SHORT_DATE_FORMAT = "Ymd"
TIME_FORMAT = "H:i"

WEASYPRINT_BASEURL = "/"

# all these permissions are created for each team,
# for example bar_team_lead, bar_team_member, etc.
BORNHACK_TEAM_PERMISSIONS = {
    "lead": "Team lead - members and permissions management",
    "member": "Team member",
    "mapper": "Team mapper - layers and feature management",
    "facilitator": "Team facilitator - facilities management",
    "infopager": "Team infopager - infopage management",
    "pos": "Team Pos - Point-of-sale report submission",
    "tasker": "Team Tasker - task management",
}
