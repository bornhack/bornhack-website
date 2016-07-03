SETTINGS = bornhack.settings.development

all: migrate superuser run

migrations:
	./manage.py makemigrations --settings=$(SETTINGS)

migrate:
	./manage.py migrate --settings=$(SETTINGS)

superuser:
	./manage.py createsuperuser --settings=$(SETTINGS)

run:
	./manage.py runserver --settings=$(SETTINGS)

.PHONY = all migrations migrate superuser run
