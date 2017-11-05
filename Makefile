all: build db_up sleep migrate bootstrap web_up

build:
	docker-compose build

db_up:
	docker-compose up -d db

migrate:
	docker-compose run web /usr/local/bin/python src/manage.py migrate

bootstrap:
	docker-compose run web /usr/local/bin/python src/manage.py bootstrap-devsite

sleep:
	echo "Sleeping to ensure that the db is up."; sleep 3

web_up:
	docker-compose up web
