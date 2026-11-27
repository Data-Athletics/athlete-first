from sqlalchemy import Select
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.cursor import TupleAny

from app.core.config import app_settings


def print_query(query: Select[TupleAny], label: str | None = None):  # pragma: no cover
    """Print SQL statement for an SQLAlechemy query"""

    if not app_settings.debug:
        return

    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )

    if label:
        message = f"Compiled SQL [{label}]:"
    else:
        message = "Compiled SQL:"

    print(message, f"\n{sql}")
