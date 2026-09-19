import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import app_settings, db_settings
from app.core.database import ModelBase, get_db_session, get_engine
from app.main import app


@pytest.fixture(scope="session", name="settings", autouse=True)
async def settings_fixture():
    """Override settings with testing values."""

    app_settings.env = "test"
    db_settings.name = "test"


@pytest.fixture(scope="session", name="engine")
async def engine_fixture(settings):
    """Create engine and setup database."""

    engine = get_engine()

    # Ensure database is clean first
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.drop_all)
        await conn.run_sync(ModelBase.metadata.create_all)

    yield engine

    # Finally, drop all tables after all tests have run
    async with engine.connect() as conn:
        await conn.run_sync(ModelBase.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function", name="db")
async def session_fixture(engine):  # noqa: ARG001
    """Create test db session with postgres test database."""

    async for db_session in get_db_session():
        try:
            # Before each test, truncate db tables
            conn = await db_session.connection()
            inspector = await conn.run_sync(inspect)
            target_tables = await conn.run_sync(
                lambda _: inspector.get_sorted_table_and_fkc_names()  # noqa: B023
            )
            target_table_names = [
                table[0] for table in target_tables if table[0] is not None
            ]

            for table in target_table_names:
                await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

            yield db_session

            # After each test, roll back the changes
            await db_session.rollback()
        except Exception:
            await db_session.rollback()


@pytest.fixture(scope="function", name="client")
async def client_fixture(db: AsyncSession):
    """Create test api client with custom dependency overrides."""

    async def get_session_override():
        async with db.begin_nested() as transaction:
            yield transaction.session

    # Make sure the api functions get the test database
    app.dependency_overrides[get_db_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test" + app_settings.api_prefix,
    ) as client:
        yield client

    # Reset the dependency injection overrides
    app.dependency_overrides.clear()
