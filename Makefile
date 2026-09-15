.PHONY: dev run build test prod

env:
	

build: env
	docker-compose build

run: env
	docker-compose up --force-recreate

dev: env build run

test:
	docker compose run --rm athlete-first sh -c "pytest"

prod: env
	docker-compose up --build

