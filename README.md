# Bornhack

Django project to power Bornhack.

Features do not include:
- Create camp
- Control expenses for a camp
- Manage signups for attendees for a camp
- ...

## Quickstart


Create a virtual environment and activate it:

    $ virtualenv venv
    $ source venv/bin/activate

Install dependencies:

    (venv) $ pip install -r requirements/development.txt

Copy environment file and change settings like DATABASE_URL:

    (venv) $ cp bornhack/settings/env.dist bornhack/settings/.env

Run `make`

    (venv) $  make

Which is equivalent with this:

    (venv) $ ./manage.py migrate --settings=bornhack.settings.development
    (venv) $ ./manage.py createsuperuser --settings=bornhack.settings.development
    (venv) $ ./manage.py runserver --settings=bornhack.settings.development
