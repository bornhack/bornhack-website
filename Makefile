DOCKER_COMPOSE = COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose -p bornhack -f docker/docker-compose.yml
DOCKER_RUN = ${DOCKER_COMPOSE} run -u `id -u`
MANAGE_EXEC = ${DOCKER_COMPOSE} exec app python /app/src/manage.py
MANAGE_RUN = ${DOCKER_RUN} app python /app/src/manage.py
PARALLEL=4
TEST_OPTIONS = --failfast --keepdb --parallel ${PARALLEL}
TEST_TO_RUN = .

init: copy_env_file update_submodules migrate bootstrap_devsite

run:
	${DOCKER_COMPOSE} up

migrate:
	${MANAGE_RUN} $@ ${ARGS}

makemigrations:
	${MANAGE_RUN} $@ ${ARGS}

bootstrap_devsite:
	${MANAGE_RUN} $@ ${ARGS}

shell:
	${MANAGE_RUN} $@ ${ARGS}

manage:
	${MANAGE_RUN} ${COMMAND}

test:
	${DOCKER_RUN} app \
		bash -c "cd /app/src/; python manage.py test $(TEST_OPTIONS) ${TEST_TO_RUN}"

build_docker_image:
	${DOCKER_COMPOSE} build app

copy_env_file:
	test -f src/bornhack/environment_settings.py || cp src/bornhack/environment_settings.py.dist.dev src/bornhack/environment_settings.py
	test -f docker/.env || cp docker/.env.dev docker/.env

update_submodules:
	git submodule update --init --recursive
