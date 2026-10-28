from pathlib import Path


def load_sql(sql_directory: Path, filename: str) -> str:
    """Load a SQL file relative to the caller's SQL directory."""

    return (sql_directory / filename).read_text(encoding="utf-8")
