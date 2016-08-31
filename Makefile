SETTINGS = bornhack.settings.development

all: migrate superuser run

migrations:
	./dev.sh makemigrations --settings=$(SETTINGS)

migrate:
	./dev.sh migrate --settings=$(SETTINGS)

superuser:
	./dev.sh createsuperuser --settings=$(SETTINGS)

run:
	./dev.sh runserver --settings=$(SETTINGS)

.PHONY = all migrations migrate superuser run
