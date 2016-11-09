from .base import *
import environ
env = environ.Env()
environ.Env.read_env()

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# INSTALLED_APPS += ['debug_toolbar', ]

