# AthleteFirst

A platform focused on providing athletes with autonomy over the biometric data collected by their wearables.

## Quick Start

Set up your virtual environment: python -m venv .venv

Activate virtual environment: source .venv/Scripts/activate (depends based on OS)

Ensure docker is downloaded and running

To run development setup: make dev

To load the demo teams, metric requirements, consent states, and 30 days of
biometric data for each seeded player:

```bash
make seed
```

To reset the demo database and reload everything from scratch before a demo:

```bash
make demo-reset
```

The seeded accounts use the password `changeme`:

- `coach@email.com`: configure metric requests from the Team page.
- `coach2@email.com`: assistant coach on Team Alpha only.
- `player@email.com`: Team Alpha has an invalid BPM policy and should show the red attention dot.
- `player2@email.com`: Team Beta has valid consent; upload metrics manually if needed.
- `player3@email.com`: approved player on Team Alpha.
- `player4@email.com`: shared player on both Team Alpha and Team Beta.

View API docs at http://localhost:8000/api/v1/docs

## Conventions

### DTOs

Naming: `[verb][resource][adjective]`

## CLI Commands

Run CLI commands through the application container after the database is ready.

Initialize the database (only if it is not initialized):

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py init"
```

Create a user:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py create-user --username user --name 'Example User' --password changeme --height 70 --weight 170 --sex Male --age 22"
```

Create an admin user:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py create-user --username admin --name 'Example Admin' --password changeme --height 70 --weight 170 --sex Male --age 22 --admin"
```

Create a team:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py create-team --name 'Example Team'"
```

Create a team membership:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py create-membership --user-id 1 --team-id 1"
```

Approve a team membership:

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py approve-membership --user-id 1 --team-id 1"
```

Upload biometric data (duplicate rows are skipped and counted):

```bash
docker compose run --rm athlete-first sh -c "bash /scripts/wait-for-db.sh && uv run python app/cli.py upload-biometrics --user-id 1 --file tests/fixtures/noop_mock.csv"
```

Generate one month of sample biometric data:

```bash
python3 utilities/generate_biometrics.py
```

This writes a timestamped file such as `~/biometrics_one_month_2026-11-16T03-45-45.199Z.csv`. Use `--output-dir` to choose a directory, or `--output` to provide an exact file path. `--days` and `--sample-seconds` customize the generated data.

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
