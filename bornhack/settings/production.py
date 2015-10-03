from .base import *
import environ

env = environ.Env(
    ENGINE='django.db.backends.postgres_psycopg2',
)
environ.Env.read_env()

SECRET_KEY = env('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

DATABASES = {
    'default': env.db(),
}
