.PHONY: dev run build test prod clean demo-reset

build:
	docker compose build

run:
	docker compose up --force-recreate --renew-anon-volumes

dev: build run

# Seeds two teams with a shared coach, a Team Alpha-only coach, three Team
# Alpha player memberships, and two Team Beta player memberships.
seed:
	docker compose run --rm athlete-first sh -c "\
		bash /scripts/wait-for-db.sh && \
		uv run python app/cli.py init && \
		uv run python app/cli.py create-user --username player@email.com --name 'First Player' --password changeme --height 71 --weight 138 --sex male --age 21 && \
		uv run python app/cli.py create-user --username player2@email.com --name 'Second Player' --password changeme --height 68 --weight 150 --sex female --age 22 && \
		uv run python app/cli.py create-user --username player3@email.com --name 'Third Player' --password changeme --height 70 --weight 160 --sex male --age 23 && \
		uv run python app/cli.py create-user --username coach@email.com --name 'Coach' --password changeme --staff && \
		uv run python app/cli.py create-user --username player4@email.com --name 'Fourth Player' --password changeme --height 72 --weight 175 --sex female --age 24 && \
		uv run python app/cli.py create-user --username coach2@email.com --name 'Assistant Coach' --password changeme --staff && \
		uv run python app/cli.py create-team --name 'Team Alpha' && \
		uv run python app/cli.py create-team --name 'Team Beta' && \
		uv run python app/cli.py create-membership --user-id 1 --team-id 1 --role athlete --status approve && \
		uv run python app/cli.py create-membership --user-id 2 --team-id 2 --role athlete --status approve && \
		uv run python app/cli.py create-membership --user-id 5 --team-id 1 --role athlete --status approve && \
		uv run python app/cli.py create-membership --user-id 5 --team-id 2 --role athlete --status approve && \
		uv run python app/cli.py create-membership --user-id 4 --team-id 1 --role coach --status approve && \
		uv run python app/cli.py create-membership --user-id 4 --team-id 2 --role coach --status approve && \
		uv run python app/cli.py create-membership --user-id 6 --team-id 1 --role coach --status approve && \
		uv run python app/cli.py create-membership --user-id 3 --team-id 1 --role athlete --status approve && \
		uv run python app/cli.py upload-biometrics --user-id 1 --file seed_data/biometrics/player1.csv && \
		uv run python app/cli.py upload-biometrics --user-id 2 --file seed_data/biometrics/player2.csv && \
		uv run python app/cli.py upload-biometrics --user-id 3 --file seed_data/biometrics/player3.csv && \
		uv run python app/cli.py upload-biometrics --user-id 5 --file seed_data/biometrics/player4.csv && \
		uv run python app/cli.py seed-data-sharing \
	"

test:
	docker compose run --rm athlete-first sh -c "/scripts/wait-for-db.sh test && pytest"

prod:
	docker compose up --build

clean:
	docker compose down -v

demo-reset: clean seed

