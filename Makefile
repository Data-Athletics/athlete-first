.PHONY: dev run build test prod clean

build:
	docker compose build

run:
	docker compose up --force-recreate --renew-anon-volumes

dev: build run

# Seeds two teams with a shared coach, two approved athletes on Team Alpha,
# one approved athlete on Team Beta, and one athlete without a team.
seed:
	docker compose run --rm athlete-first sh -c "\
		bash /scripts/wait-for-db.sh && \
		uv run python app/cli.py create-user --username player@email.com --password changeme --height 71 --weight 138 --sex male --age 21 && \
		uv run python app/cli.py create-user --username player2@email.com --password changeme --height 68 --weight 150 --sex female --age 22 && \
		uv run python app/cli.py create-user --username player3@email.com --password changeme --height 70 --weight 160 --sex male --age 23 && \
		uv run python app/cli.py create-user --username coach@email.com --password changeme --staff && \
		uv run python app/cli.py create-team --name 'Team Alpha' && \
		uv run python app/cli.py create-team --name 'Team Beta' && \
		uv run python app/cli.py create-membership --user-id 1 --team-id 1 --role athlete --status approve && \
		uv run python app/cli.py create-membership --user-id 2 --team-id 1 --role athlete --status approve && \
		uv run python app/cli.py create-membership --user-id 1 --team-id 2 --role athlete --status approve && \
		uv run python app/cli.py create-membership --user-id 4 --team-id 1 --role coach --status approve && \
		uv run python app/cli.py create-membership --user-id 4 --team-id 2 --role coach --status approve \
	"

test:
	docker compose run --rm athlete-first sh -c "/scripts/wait-for-db.sh test && pytest"

prod:
	docker compose up --build

clean:
	docker compose down -v

