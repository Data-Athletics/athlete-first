.PHONY: dev run build test prod

build:
	docker compose build

run:
	docker compose up --force-recreate --renew-anon-volumes

dev: build run

test:
	docker compose run --rm athlete-first sh -c "/scripts/wait-for-db.sh test && pytest"

prod:
	docker compose up --build

