from app.biometrics.types import NoopData
from app.core.dependencies import AsyncSessionDep


async def bulk_upload_noop_data(db: AsyncSessionDep, noop_data: NoopData):
    """Bulk uploads noop data model to the database"""

    models = noop_data.to_models()
    db.add_all(models.to_list())
    await db.flush()
