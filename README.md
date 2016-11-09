# Bornhack

Django project to power Bornhack. Features include news, villages, webshop, and more.

## Quickstart

### Virtualenv
Create a Python 2.7 virtual environment and activate it:
    $ virtualenv venv
    $ source venv/bin/activate

### System libraries
Install system dependencies (method depends on OS):
- postgresql headers (for psychopg2)
- libjpeg (for pdf generation)

### Python packages
Install pip packages (pick either development or production):
    (venv) $ pip install -r requirements/development.txt
    (venv) $ pip install -r requirements/production.txt

### Configuration file
Copy environment file template and change settings:
    (venv) $ cp bornhack/settings/env.dist bornhack/settings/.env

### Database
Is this a new installation? Initialize the database:
    (venv) $ ./manage.py migrate --settings=bornhack.settings.development
    (venv) $ ./manage.py createsuperuser --settings=bornhack.settings.development

### Done
Is this for local development? Start the Django devserver:
    (venv) $ ./manage.py runserver --settings=bornhack.settings.development

Otherwise start uwsgi or similar to serve the application.

