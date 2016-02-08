from .base import *
import environ

env = environ.Env()

environ.Env.read_env()

DEBUG = False
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(',')

DATABASES = {
    'default': env.db(),
}
