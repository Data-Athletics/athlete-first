from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.biometrics.router import biometrics_router
from app.core.config import app_settings
from app.core.database import ModelBase, get_engine
from app.observability import router as observability_router
from app.user import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Runs on server startup and yields until server shutdown."""

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

    yield


app = FastAPI(
    lifespan=lifespan,
    docs_url=app_settings.api_prefix + "/docs",
    openapi_url=app_settings.api_prefix + "/openapi.json",
)


router = APIRouter(prefix=app_settings.api_prefix)
app.include_router(router)

router.include_router(observability_router, prefix="/observability")
router.include_router(user_router, prefix="/user")
router.include_router(biometrics_router, prefix="/biometrics")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=app_settings.allow_origins,
    allow_methods=app_settings.allow_methods,
    allow_headers=app_settings.allow_headers,
    expose_headers=app_settings.expose_headers,
)


@app.get("/")
async def index():
    return {"message": "Systems Operational"}
