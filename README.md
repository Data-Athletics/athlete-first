# AthleteFirst

A platform focused on providing athletes with autonomy over the biometric data collected by their wearables.

# Quick Start

Set up your virtual environment: python -m venv .venv

Activate virtual environment: source .venv/Scripts/activate (depends based on OS)

Ensure docker is downloaded and running

To run development setup: make dev

View API docs at http://localhost:8000/api/v1/docs

## CLI Commands

Run CLI commands through the application container after the database is ready.

Initialize the database (only if it is not initialized):

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py init"
```

Create a user:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py create-user --username user --password changeme --height 70 --weight 170 --sex Male --age 22"
```

Create an admin user:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py create-user --username admin --password changeme --height 70 --weight 170 --sex Male --age 22 --admin"
```

Upload biometric data:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py upload-biometrics --user-id 1 --file tests/fixtures/noop_mock.csv"
```

Calculate HRV:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py hrv --user-id 1 --end-time 2025-04-27T14:46:47.336Z"
```

Calculate resting heart rate:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py rhr --user-id 1 --start-time 2025-04-27T14:00:00Z --end-time 2025-04-27T15:00:00Z"
```

Calculate skin temperature delta:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py skin-temp-delta --user-id 1"
```

Calculate respiratory rate:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py respiratory-rate --user-id 1"
```

Calculate effort/strain:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py effort --user-id 1"
```

Calculate estimated calories:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py calories --user-id 1"
```

Get BPM data over an interval:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py bpm --user-id 1 --start-time 2025-04-27T14:46:47.000Z --end-time 2025-04-27T14:46:47.240Z"
```

Use ISO 8601 timestamps for date/time parameters, for example:

```text
2025-04-27T14:46:47.336Z
```