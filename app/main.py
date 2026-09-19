from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import app_settings
from app.core.database import ModelBase, get_engine
from app.core.dtos import SimpleResponseDTO
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
    root_path=app_settings.api_prefix,
)


router = APIRouter()
app.include_router(router)

router.include_router(observability_router, prefix="/observability")
router.include_router(user_router, prefix="/user")


@app.exception_handler(Exception)
async def handle_exceptions(request: Request, exc: Exception):
    """Catch exceptions and return them in a consistent manner"""

    detail = None
    headers = None
    code = None

    if isinstance(exc, HTTPException):
        detail = exc.detail
        headers = exc.headers
        code = exc.status_code
    elif isinstance(exc, NotImplementedError):
        detail = "Not Implemented"
        code = status.HTTP_501_NOT_IMPLEMENTED
    else:
        detail = "Uncaught exception"
        code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        content=jsonable_encoder(
            SimpleResponseDTO(detail=detail, code=code).model_dump()
        ),
        headers=headers,
    )


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
