from app.biometrics.types import NoopData
from app.core.dependencies import AsyncSessionDep


async def bulk_upload_noop_data(
    db: AsyncSessionDep, user_id: int, noop_data: NoopData
) -> None:
    """Bulk uploads noop data model to the database"""

    models = noop_data.to_models(user_id)
    db.add_all(models.to_list())
    await db.flush()
