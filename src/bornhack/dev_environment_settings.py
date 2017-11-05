# This file is intended for easing the creation of a local development setup
SECRET_KEY = "something-very-random"
ALLOWED_HOSTS = "*"
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bornhack',
        'USER': 'bornhack',
        'PASSWORD': 'bornhack',
        'HOST': 'db',
    },
}
DEBUG=True
WKHTMLTOPDF_CMD="wkhtmltopdf"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgiref.inmemory.ChannelLayer",
        "ROUTING": "bornhack.routing.channel_routing",
        "CONFIG": {}
    },
}
CAMP_REDIRECT_PERCENT=40
