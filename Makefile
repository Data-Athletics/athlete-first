.PHONY: dev run build test prod

env:
	

build: env
	docker-compose build

run: env
	docker-compose up --force-recreate

dev: env build run

test:
	docker compose run --rm athlete-first sh -c "/scripts/wait-for-db.sh test && pytest"

prod: env
	docker-compose up --build

