# Bornhack

Django project to power Bornhack. Features include news, villages, webshop, and more.

## Quickstart

### Virtualenv
Create a Python 2.7 virtual environment and activate it:
```
$ virtualenv venv
$ source venv/bin/activate
```

### System libraries
Install system dependencies (method depends on OS):
- postgresql headers (for psychopg2):
  - Debian: ?
  - FreeBSD: ?
- libjpeg (for pdf generation)
  - Debian: libjpeg-dev
  - FreeBSD: ?

### Python packages
Install pip packages:
```
    (venv) $ pip install -r requirements.txt
```

### Configuration file
Copy environment file template and change settings as needed:
```
    (venv) $ cp bornhack/settings/env.dist bornhack/settings/.env
```

### Database
Is this a new installation? Initialize the database:
```
    (venv) $ ./manage.py migrate
```

Is this for local development? Bootstrap the database with dummy data and users:
```
    (venv) $ ./manage.py bootstrap-devsite
```

### Done
Is this for local development? Start the Django devserver:
```
    (venv) $ ./manage.py runserver
```

Otherwise start uwsgi or similar to serve the application.

Enjoy!

