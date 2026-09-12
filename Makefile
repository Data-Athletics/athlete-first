.PHONY: dev run build test prod

env:
	cp example.env .env

build: env
	docker-compose build

run: env
	docker-compose up --force-recreate --renew-anon-volumes

dev: env build run

test:
	docker-compose -f docker-compose.test.yaml up --build --force-recreate --renew-anon-volumes

prod: env
	docker-compose up --build

