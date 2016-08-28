#!/bin/bash

# Directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

DEV_DIR="$DIR/.dev"

if [ ! -d "$DEV_DIR"]
then
    mkdir -p "$DEV_DIR"
fi

export MEDIA_ROOT="$DEV_DIR/media/"
export EPAY_MERCHANT_NUMBER="123"
export EPAY_MD5_SECRET="123"
export COINIFY_API_KEY="123"
export COINIFY_API_SECRET="123"
export COINIFY_IPN_SECRET="123"
export PDF_LETTERHEAD_FILENAME="bornhax.pdf"
export BANKACCOUNT_IBAN="femfladeflødeboller"
export BANKACCOUNT_SWIFTBIC="goldmansachs"
export BANKACCOUNT_REG="1234"
export BANKACCOUNT_ACCOUNT="56789"
export TICKET_CATEGORY_ID="1"
export SECRET_KEY="muchsecret"
export ALLOWED_HOSTS="127.0.0.1"
export DATABASE_URL="sqlite:///$DEV_DIR/dev.db"
export EMAIL_HOST="localhost"
export EMAIL_PORT="22"
export EMAIL_HOST_USER="$USER"
export EMAIL_HOST_PASSWORD=""
export EMAIL_USE_TLS=""
export DEFAULT_FROM_EMAIL="bornhax@localhost"
export ARCHIVE_EMAIL=""

python manage.py $@ --settings=bornhack.settings.development
