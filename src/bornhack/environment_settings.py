# make this a long 100+ chars random string
SECRET_KEY = 'secret'

# debug settings - remember to set allowed_hosts if debug is disabled
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database settings
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bornhackdb',
        'USER': 'bornhack',
        'PASSWORD': 'bornhack',
        'HOST': '127.0.0.1',
    },
}

### changes below here are only needed for production

# email settings
EMAIL_HOST='mailhost.example.com'
EMAIL_PORT=587
EMAIL_HOST_USER='mymailuser'
EMAIL_HOST_PASSWORD='mymailpassword'
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL='noreply@example.com'
ARCHIVE_EMAIL='archive@example.com'

ADMINS=(
    ('sysadm', 'sysadm@example.com')
)

# misc settings
TIME_ZONE='Europe/Copenhagen'
MEDIA_ROOT='/path/to/media/root/outside/django/root/'
PDF_ARCHIVE_PATH='/usr/local/www/pdf_archive/'

# PSP settings
EPAY_MERCHANT_NUMBER=123
EPAY_MD5_SECRET='abc'
COINIFY_API_KEY='123'
COINIFY_API_SECRET='123'
COINIFY_IPN_SECRET='123'

# shop settings
PDF_LETTERHEAD_FILENAME='letterhead.pdf'
BANKACCOUNT_IBAN='123'
BANKACCOUNT_SWIFTBIC='123'
BANKACCOUNT_REG='123'
BANKACCOUNT_ACCOUNT='123'

# schedule settings
SCHEDULE_MIDNIGHT_OFFSET_HOURS=6
SCHEDULE_TIMESLOT_LENGTH_MINUTES=30

# irc bot settings
IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS=60
IRCBOT_NICK='BornHack'
IRCBOT_SCHEDULE_ANNOUNCE_CHANNEL='#test'
IRCBOT_SERVER_HOSTNAME='ircd.tyknet.dk'
IRCBOT_SERVER_PORT=6697
IRCBOT_SERVER_USETLS=True

