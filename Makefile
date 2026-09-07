.PHONY: dev run build test prod

env:
	cp example.env .env

build: env
	docker-compose build

run: env
	docker-compose up --force-recreate

dev: env build run

test:
	docker-compose -f docker-compose.test.yaml up --build --force-recreate

prod: env
	docker-compose up --build

