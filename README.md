# Bornhack

[![tests](https://github.com/bornhack/bornhack-website/actions/workflows/main.yml/badge.svg)](https://github.com/bornhack/bornhack-website/actions)
[![codecov](https://codecov.io/gh/bornhack/bornhack-website/branch/master/graph/badge.svg)](https://codecov.io/gh/bornhack/bornhack-website)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bornhack/bornhack-website/master.svg)](https://results.pre-commit.ci/latest/github/bornhack/bornhack-website/master)

Django project to power Bornhack. Features include news, villages, webshop, and more.

## Contributing
Request changes, report bugs, submit other issues
at [the issue tracker](https://github.com/bornhack/bornhack-website/issues),
by email to one of the developers, or the #bornhack-website IRC channel.

Submit changes [here](https://github.com/bornhack/bornhack-website/pulls),
by email to one of the developers, or the #bornhack-website IRC channel.

## Development setup

### Using docker

There is a Docker/docker-compose setup in the docker/ directory to ease development.

The `Makefile` contains commands to help running commands in the docker container.

#### Initialise the development setup:

Copy dev settings (will overwrite existing), make sure submodules are updated, migrate and bootstrap devsite in one command:

    make init

#### Run django management commands in the container

To run commands in the container use the following

    make manage COMMAND=<command>

Common commands exist as own Makefile entries:

    make shell           # ./manage.py shell
    make makemigrations  # ./manage.py makemigrations
    make migrate         # ./manage.py migrate

Run the project using

    make run

### Manual setup

#### Clone the repo
Clone with --recursive to include submodules:

    git clone --recursive https://github.com/bornhack/bornhack-website

If you already cloned the repository without --recursive, you can change into the directory and add the submodules with:

    git submodule update --init --recursive

#### Virtualenv
Create a Python 3.7 virtual environment and activate it:
```
$ virtualenv venv -p python3.7
$ source venv/bin/activate
```

If you installed python3 using Homebrew on macOS, you will need to install virtualenv by running the following command first:
```
pip3 install virtualenv
```

#### System libraries
Install system dependencies (method depends on OS):
- postgresql headers (for psycopg2):

  - OpenBSD: pkg_add postgresql-client-11
  - Debian: libpq-dev
  - FreeBSD: databases/postgresql11-client
  - macOS: If using the PostgreSQL.app, the headers are included, only path needs to be added
- libjpeg (for pdf generation)
  - OpenBSD: pkg_add jpeg
  - Debian: libjpeg-dev
  - FreeBSD: graphics/jpeg-turbo
  - macOS: brew install libjpeg
- libmagic (might already be installed)
  - OpenBSD: pkg_add libmagic
  - macOS: brew install libmagic
- GDAL (might already be installed)
  - macOS: brew install gdal
- wkhtmltopdf (also for pdf generation):
  - OpenBSD: pkg_add wkhtmltopdf
  - Debian: wkhtmltopdf
  - FreeBSD: converters/wkhtmltopdf
  - macOS: install from https://wkhtmltopdf.org/
- fonts
  - Debian: ?
  - FreeBSD: x11-fonts/webfonts
  - macOS: ?
- Not handled by pip
  - OpenBSD: py3-cryptography py3-zope.event

#### Python packages
Install pip packages:
```
(venv) $ pip install -r src/requirements/dev.txt
```

#### Postgres

You need to have a running Postgres instance (sqlite or mysql or others can't be used, because we use Postgres-specific fields and PostGIS/GeoDjango). Install Postgres and PostGIS, and add a database `bornhack` (or whichever you like) with some way for the application to connect to it, for instance adding a user with a password. Connect to the database as a superuser and run `create extension postgis`. The postgres version in production is 12 and the postgis version in production is 2.5. The minimum postgres version is 10, because we use GIST indexes on uuid fields (for ExclusionConstraints). You might also need `create extension btree_gist`, again as a superuser.

#### Configuration file

Copy dev environment settings file and change settings as needed:

```
(venv) $ cp src/bornhack/environment_settings.py.dist.dev src/bornhack/environment_settings.py
```

Edit the configuration file, setting up `DATABASES` matching your Postgres settings.

#### Database
Is this a new installation? Initialize the database:

```
(venv) $ python src/manage.py migrate
```

Is this for local development? Bootstrap the database with dummy data and users:

```
(venv) $ python src/manage.py bootstrap_devsite
```

This creates some user accounts. Run the following command to see their email
addresses and passwords.

```
(venv) $ python src/manage.py dbshell -- -c 'select email, username as password from auth_user;'
```

If you run software other than GNU/Linux or on architecture other than amd64,
you may get an error like this.

```
OSError: [Errno 8] Exec format error: '/srv/opt/bornhack/.local/lib/python3.9/site-packages/pulp/apis/../solverdir/cbc/linux/64/cbc'
```

In such case, skip the autoscheduler like so.

```
(venv) $ python src/manage.py bootstrap_devsite --skip-auto-scheduler
```

#### Done
Is this for local development? Start the Django devserver:
```
(venv) $ python src/manage.py runserver
```

Otherwise start uwsgi or similar to serve the application.

Enjoy!


## OIDC IDP

The BornHack website can act as an OIDC IDP. You are welcome to use it for your projects.


### OIDC Scopes and User Claims
The website has a view to inspect which OIDC user claims are returned when using the various claim scopes. It can be accessed at https://bornhack.dk/profile/oidc/


### OIDC User Claims Source Code

The supported standard and custom OIDC user claims can be seen in `bornhack/oauth_validators.py` https://github.com/bornhack/bornhack-website/blob/master/src/bornhack/oauth_validators.py


### OIDC Scopes Source Code

Supported oauth2 scopes are divided into standard OIDC claim scopes, custom OIDC claim scopes, and API scopes. The current list of supported scopes can be seen in the `OAUTH2_PROVIDER["SCOPES"]` dict in `bornhack/settings.py` https://github.com/bornhack/bornhack-website/blob/master/src/bornhack/settings.py


## Notes

### Running tests
If your database user in your dev setup is not a postgres superuser you will encounter permission errors when the migrations try to create extensions "btree_gist" and "postgis". You can solve this by connecting to the "template1" database as the postgres superuser and creating the extensions there, which means they will be automatically loaded for all newly created databases.

### Add a camp

First do a commit with:

* A frontpage, `{camp-slug}_camp_detail.html`, to `camps/templates`.
* A `static_src/img/{camp-slug}/logo` and add two logos:
    * `{camp-slug}-logo-large.png`
    * `{camp-slug}-logo-small.png`

Then go to the admin interface and add the camp.


## Contributors
* Alexander Færøy https://github.com/ahf
* Benjamin Bach https://github.com/benjaoming
* coral https://github.com/coral
* Flemming Jacobsen https://github.com/batmule
* Florian Klink https://github.com/flokli
* Henrik Kramshøj https://github.com/kramse
* Janus Troelsen https://github.com/ysangkok
* Jeppe Ernst https://github.com/Ern-st
* Jonty Wareing https://github.com/Jonty
* Kasper Christensen https://github.com/fALKENdk
* klarstrup https://github.com/klarstrup
* kugg https://github.com/kugg
* lgandersen https://github.com/lgandersen
* RadicalPet https://github.com/RadicalPet
* Reynir Björnsson https://github.com/reynir
* Ronni Elken Lindsgaard https://github.com/rlindsgaard
* Stephan Telling https://github.com/Telling
* Thomas Flummer https://github.com/flummer
* Thomas Steen Rasmusssen https://github.com/tykling
* Víðir Valberg Guðmundsson https://github.com/valberg
* Ximin Luo https://github.com/infinity0
* zarya https://github.com/zarya
