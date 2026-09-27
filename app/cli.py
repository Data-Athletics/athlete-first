"""CLI Utilities

Ref: https://typer.tiangolo.com/
"""

import asyncio
from functools import wraps
from typing import Annotated

import typer

from app.auth.services import get_password_hash
from app.core.database import (
    ModelBase,
    get_db_session_context,
    get_engine,
)
from app.user.models import User

app = typer.Typer()


def async_command(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@app.command()
@async_command
async def init():
    """Initialize the application"""

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)


@app.command()
@async_command
async def create_admin_user(
    username: Annotated[str, typer.Option(help="Username of the new user")],
    password: Annotated[str, typer.Option(help="Password for the new user")],
):
    async with get_db_session_context() as db:
        hash = get_password_hash(password)
        user = User(username=username, hashed_password=hash, is_admin=True)
        db.add(user)
        await db.commit()

        print(f"Created user: <User id={user.id} is_admin=True username='{username}'>")


if __name__ == "__main__":
    app()
