# Bornhack

Django project to power Bornhack.

Features do not include:
- Create camp
- Control expenses for a camp
- Manage signups for attendees for a camp
- ...

## Quickstart

Create a Python 2.7 virtual environment and activate it:

    $ virtualenv venv
    $ source venv/bin/activate

Install dependencies:

    (venv) $ pip install -r requirements/development.txt

Copy environment file and change settings like DATABASE_URL:

    (venv) $ cp bornhack/settings/env.dist bornhack/settings/.env

Run `make` (removing USE_SQLITE=1 if you want to use postgres)

    (venv) $ SQLITE=1 make

Which is equivalent with this:

    (venv) $ ./manage.py migrate --settings=bornhack.settings.development
    (venv) $ ./manage.py createsuperuser --settings=bornhack.settings.development
    (venv) $ ./manage.py runserver --settings=bornhack.settings.development

### Setting up Postgres

Using Postgres is only necessary for purposes of the special
[JSONField](https://docs.djangoproject.com/en/1.10/ref/contrib/postgres/fields/).
The field is active on our shop mainly, so you can still develop things for most
parts of the site without installing Postgres.

To use default settings and make commands, create a user `bornhack`, password
`bornhack` and database `bornhack_dev` to use default setttings.
