"""CLI Utilities

Ref: https://typer.tiangolo.com/
"""

import asyncio
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Annotated

import typer

from app.auth.services import get_password_hash
from app.biometrics.decoder import decode_noop_csv
from app.biometrics.services import (
    bulk_bpm_data,
    bulk_upload_noop_data,
    calculate_calories,
    calculate_effort_strain,
    calculate_hrv,
    respiratory_rate,
    rhr_over_interval,
    skin_temp_delta,
)
from app.core.database import ModelBase, get_db_session_context, get_engine
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
async def create_user(
    username: Annotated[str, typer.Option(help="Username of the new user")],
    password: Annotated[str, typer.Option(help="Password of the new user")],
    height: Annotated[float | None, typer.Option(help="Height in inches")] = None,
    weight: Annotated[float | None, typer.Option(help="Weight in pounds")] = None,
    sex: Annotated[
        str | None, typer.Option(help="Sex of the user: Male or Female")
    ] = None,
    age: Annotated[int | None, typer.Option(help="Age in years")] = None,
    is_admin: Annotated[
        bool, typer.Option("--admin", help="Create the user as an admin")
    ] = False,
):
    """Create a new application user."""

    if sex is not None and sex not in ("Male", "Female"):
        raise typer.BadParameter("Sex must be either 'Male' or 'Female'")

    async with get_db_session_context() as db:
        hashed_password = get_password_hash(password)

        user = User(
            username=username,
            hashed_password=hashed_password,
            height=height,
            weight=weight,
            sex=sex,
            age=age,
            is_admin=is_admin,
        )

        db.add(user)
        await db.commit()

        print(
            f"Created user: <User id={user.id} "
            f"is_admin={user.is_admin} "
            f"username='{user.username}' "
            f"height={user.height} "
            f"weight={user.weight} "
            f"sex={user.sex} "
            f"age={user.age}>"
        )


def parse_datetime(value: str) -> datetime:
    """Parse an ISO-8601 datetime."""

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise typer.BadParameter(
            "Datetime must be ISO-8601, e.g. 2025-04-27T14:46:47.336Z"
        ) from e


@app.command()
@async_command
async def upload_biometrics(
    user_id: Annotated[int, typer.Option(help="User ID to upload biometric data for")],
    file: Annotated[
        Path,
        typer.Option(
            exists=True, dir_okay=False, readable=True, help="Path to NOOP CSV file"
        ),
    ],
):
    """Upload biometric data from a NOOP CSV file."""

    if file.suffix.lower() != ".csv":
        raise typer.BadParameter("File must be a CSV file.")

    async with get_db_session_context() as db:
        user = await db.get(User, user_id)

        if user is None:
            raise typer.BadParameter(f"User {user_id} does not exist.")

        with file.open("rb") as csv_file:
            noop_data = decode_noop_csv(csv_file)

        await bulk_upload_noop_data(db, user_id, noop_data)

        await db.commit()

    print(f"Uploaded biometrics: <User id={user_id} file='{file}'>")


@app.command()
@async_command
async def hrv(
    user_id: Annotated[int, typer.Option(help="User ID")],
    end_time: Annotated[str, typer.Option(help="End time in ISO-8601 format")],
):
    """Calculate HRV for a user."""

    end = parse_datetime(end_time)

    async with get_db_session_context() as db:
        hrv_value, start, end = await calculate_hrv(db, user_id, end)

    print(f"HRV: <User id={user_id} hrv={hrv_value} start='{start}' end='{end}'>")


@app.command()
@async_command
async def rhr(
    user_id: Annotated[int, typer.Option(help="User ID")],
    start_time: Annotated[str, typer.Option(help="Start time in ISO-8601 format")],
    end_time: Annotated[str, typer.Option(help="End time in ISO-8601 format")],
):
    """Calculate resting heart rate for a user."""

    start = parse_datetime(start_time)
    end = parse_datetime(end_time)

    if start > end:
        raise typer.BadParameter("Start time must be less than end time.")

    async with get_db_session_context() as db:
        rhr_value, start, end = await rhr_over_interval(db, user_id, start, end)

    print(f"RHR: <User id={user_id} rhr={rhr_value} start='{start}' end='{end}'>")


@app.command("skin-temp-delta")
@async_command
async def skin_temp_delta_command(
    user_id: Annotated[int, typer.Option(help="User ID")],
):
    """Calculate skin temperature delta for a user."""

    async with get_db_session_context() as db:
        delta = await skin_temp_delta(db, user_id)

    print(f"Skin temp delta: <User id={user_id} skin_temp_delta={delta}>")


@app.command("respiratory-rate")
@async_command
async def respiratory_rate_command(
    user_id: Annotated[int, typer.Option(help="User ID")],
):
    """Calculate respiratory rate for a user."""

    async with get_db_session_context() as db:
        rate = await respiratory_rate(db, user_id)

    print(f"Respiratory rate: <User id={user_id} respiratory_rate={rate}>")


@app.command()
@async_command
async def effort(user_id: Annotated[int, typer.Option(help="User ID")]):
    """Calculate effort/strain for a user."""

    async with get_db_session_context() as db:
        effort_value = await calculate_effort_strain(db, user_id)

    print(f"Effort: <User id={user_id} effort={effort_value}>")


@app.command()
@async_command
async def calories(user_id: Annotated[int, typer.Option(help="User ID")]):
    """Calculate estimated calories for a user."""

    async with get_db_session_context() as db:
        user = await db.get(User, user_id)

        if user is None:
            raise typer.BadParameter(f"User {user_id} does not exist.")

        if (
            user.height is None
            or user.weight is None
            or user.sex is None
            or user.age is None
        ):
            raise typer.BadParameter(
                "User must have all of height, weight, sex, "
                "and age to calculate calories."
            )

        calorie_value = await calculate_calories(db, user_id)

    print(f"Calories: <User id={user_id} calories={calorie_value}>")


@app.command()
@async_command
async def bpm(
    user_id: Annotated[int, typer.Option(help="User ID")],
    start_time: Annotated[str, typer.Option(help="Start time in ISO-8601 format")],
    end_time: Annotated[str, typer.Option(help="End time in ISO-8601 format")],
):
    """Get BPM data for a user over an interval."""

    start = parse_datetime(start_time)
    end = parse_datetime(end_time)

    if start > end:
        raise typer.BadParameter("Start time must be less than end time.")

    async with get_db_session_context() as db:
        data = await bulk_bpm_data(db, user_id, start, end)

    print(
        f"BPM: <User id={user_id} "
        f"start='{data.start}' "
        f"end='{data.end}' "
        f"x={data.x} "
        f"y={data.y}>"
    )


if __name__ == "__main__":
    app()
