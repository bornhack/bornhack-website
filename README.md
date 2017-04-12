# Bornhack

Django project to power Bornhack. Features include news, villages, webshop, and more.

## Quickstart

### Clone the repo
Clone with --recursive to include submodules:

    git clone --recursive https://github.com/bornhack/bornhack-website


### Virtualenv
Create a Python 3 virtual environment and activate it:
```
$ virtualenv venv
$ source venv/bin/activate
```

### System libraries
Install system dependencies (method depends on OS):
- postgresql headers (for psycopg2):
  - Debian: libpq-dev
  - FreeBSD: databases/postgresql93-client 
- libjpeg (for pdf generation)
  - Debian: libjpeg-dev
  - FreeBSD: graphics/jpeg-turbo
- wkhtmltopdf (also for pdf generation):
  - Debian: wkhtmltopdf
  - FreeBSD: converters/wkhtmltopdf
- fonts
  - Debian: ?
  - FreeBSD: x11-fonts/webfonts

### Python packages
Install pip packages:
```
    (venv) $ pip install -r requirements.txt
```

### Configuration file
Copy environment settings file and change settings as needed:
```
    (venv) $ cp bornhack/settings/environment_settings.py.dist bornhack/settings/environment_settings.py
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

## Notes

### How to add a camp

Add a new camp in the admin interface and run `

```
    (venv) $ ./manage.py createcamp {camp-slug}
```
or go through the manuel process below:

* Add a new camp in the admin interface.
* Add a sponsers page, `{camp-slug}-sponsors.html`, to `sponsors/templates`.
* Add a frontpage, `{camp-slug}-camp_detail.html`, to `camps/templates`.
* Add a call for speakers page, `{camp-slug}-call_for_speakers.html`, to `program/templates`.
* Create `static_src/img/{camp-slug}/logo` and add two logos:
    * `{camp-slug}-logo-large.png`
    * `{camp-slug}-logo-small.png`

### multicamp prod migration notes

* when villages.0008 migration fails go add camp_id to all existing villages
* go to admin interface and add bornhack 2017, and set slug for bornhack 2016
* convert events to the new format (somehow)

